# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Lazy Ollama HTTP adapter with a loopback-only default boundary."""

from __future__ import annotations

import ipaddress
import json
import os
from collections.abc import Iterator, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import ModelRequest, ModelResponse, ProviderError


def _is_loopback(hostname: str | None) -> bool:
    if hostname is None:
        return False
    if hostname.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def _setting_bool(value: Any, *, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    normalized = str(value).strip().casefold()
    if normalized in {"true", "yes", "on"}:
        return True
    if normalized in {"false", "no", "off", ""}:
        return False
    raise ValueError(f"{name} must be a boolean")


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        *,
        model: str | None = None,
        settings: Mapping[str, Any] | None = None,
    ) -> None:
        config = dict(settings or {})
        self.model = model or str(config.get("model") or "") or None
        self.base_url = str(
            config.get("base_url") or os.environ.get("OLLAMA_BASE_URL") or "http://127.0.0.1:11434"
        ).rstrip("/")
        self.timeout = float(config.get("timeout", 60.0))
        self.allow_remote = _setting_bool(config.get("allow_remote", False), name="allow_remote")
        self.max_response_bytes = int(config.get("max_response_bytes", 10_000_000))
        if self.timeout <= 0:
            raise ValueError("Ollama timeout must be positive")
        if self.max_response_bytes < 1:
            raise ValueError("Ollama max_response_bytes must be positive")
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("OLLAMA_BASE_URL must not contain credentials, query, or fragment")
        if not self.allow_remote and not _is_loopback(parsed.hostname):
            raise ValueError("remote Ollama URLs require the explicit allow_remote setting")

    def _effective_model(self, request: ModelRequest) -> str:
        model = request.model or self.model or os.environ.get("CARTER_DEFAULT_MODEL")
        if not model:
            raise ProviderError(
                "No Ollama model is configured",
                provider=self.name,
                code="model_not_configured",
            )
        return model

    def _open(self, request: ModelRequest, *, stream: bool) -> Any:
        model = self._effective_model(request)
        body = {
            "model": model,
            "prompt": request.rendered_prompt,
            "system": request.system_prompt,
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        http_request = Request(  # noqa: S310  # nosec B310
            f"{self.base_url}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            # URL scheme and host are validated during construction.
            return urlopen(http_request, timeout=self.timeout)  # noqa: S310  # nosec B310
        except HTTPError as exc:
            raise ProviderError(
                f"Ollama returned HTTP {exc.code}",
                provider=self.name,
                code="http_error",
                retryable=exc.code >= 500,
            ) from exc
        except (URLError, TimeoutError) as exc:
            raise ProviderError(
                "Ollama is unavailable at the configured endpoint",
                provider=self.name,
                code="unavailable",
                retryable=True,
            ) from exc

    def generate(self, request: ModelRequest) -> ModelResponse:
        model = self._effective_model(request)
        with self._open(request, stream=False) as response:
            try:
                raw_payload = response.read(self.max_response_bytes + 1)
                if len(raw_payload) > self.max_response_bytes:
                    raise ProviderError(
                        "Ollama response exceeded the configured size limit",
                        provider=self.name,
                        code="response_too_large",
                    )
                payload = json.loads(raw_payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProviderError(
                    "Ollama returned an invalid JSON response",
                    provider=self.name,
                    code="invalid_response",
                ) from exc
        if not isinstance(payload, Mapping) or not isinstance(payload.get("response"), str):
            raise ProviderError(
                "Ollama response did not contain generated text",
                provider=self.name,
                code="invalid_response",
            )
        usage = {
            key: int(payload[key])
            for key in ("prompt_eval_count", "eval_count")
            if isinstance(payload.get(key), int)
        }
        return ModelResponse(
            text=payload["response"],
            provider=self.name,
            model=model,
            finish_reason=str(payload.get("done_reason") or "completed"),
            usage=usage,
            metadata={"deterministic": request.temperature == 0.0},
        )

    def stream(self, request: ModelRequest) -> Iterator[str]:
        with self._open(request, stream=True) as response:
            received = 0
            for raw_line in response:
                if not raw_line.strip():
                    continue
                received += len(raw_line)
                if received > self.max_response_bytes:
                    raise ProviderError(
                        "Ollama response exceeded the configured size limit",
                        provider=self.name,
                        code="response_too_large",
                    )
                try:
                    payload = json.loads(raw_line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ProviderError(
                        "Ollama returned an invalid streaming event",
                        provider=self.name,
                        code="invalid_response",
                    ) from exc
                if payload.get("error"):
                    raise ProviderError(
                        "Ollama reported a generation failure",
                        provider=self.name,
                        code="generation_failed",
                    )
                fragment = payload.get("response")
                if isinstance(fragment, str) and fragment:
                    yield fragment
