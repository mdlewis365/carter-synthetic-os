# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Lazy optional OpenAI provider adapter."""

from __future__ import annotations

import importlib
import os
from collections.abc import Mapping
from typing import Any

from .base import ChunkedProvider, ModelRequest, ModelResponse, ProviderError


class OpenAIProvider(ChunkedProvider):
    name = "openai"

    def __init__(
        self,
        *,
        model: str | None = None,
        settings: Mapping[str, Any] | None = None,
    ) -> None:
        config = dict(settings or {})
        self.model = model or str(config.get("model") or "") or None
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")

    def generate(self, request: ModelRequest) -> ModelResponse:
        model = request.model or self.model or os.environ.get("CARTER_DEFAULT_MODEL")
        api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError(
                "OPENAI_API_KEY is not configured",
                provider=self.name,
                code="missing_api_key",
            )
        if not model:
            raise ProviderError(
                "No OpenAI model is configured",
                provider=self.name,
                code="model_not_configured",
            )
        try:
            module = importlib.import_module("openai")
        except ImportError as exc:
            raise ProviderError(
                "OpenAI support is optional; install carter-synthetic-os[openai]",
                provider=self.name,
                code="missing_dependency",
            ) from exc
        try:
            client_kwargs = {"api_key": api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            client = module.OpenAI(**client_kwargs)
            response = client.responses.create(
                model=model,
                instructions=request.system_prompt or None,
                input=request.rendered_prompt,
                temperature=request.temperature,
                max_output_tokens=request.max_tokens,
            )
            text = response.output_text
            usage_object = getattr(response, "usage", None)
            usage = {
                "input_tokens": int(getattr(usage_object, "input_tokens", 0) or 0),
                "output_tokens": int(getattr(usage_object, "output_tokens", 0) or 0),
            }
        except Exception as exc:
            raise ProviderError(
                "OpenAI generation failed",
                provider=self.name,
                code="generation_failed",
                retryable=True,
            ) from exc
        return ModelResponse(str(text), self.name, model, usage=usage)
