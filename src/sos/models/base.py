# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Model-provider contracts independent of any vendor SDK."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable


class ProviderError(RuntimeError):
    """Sanitized provider failure safe to display in a public interface."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        code: str = "provider_error",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True, slots=True, init=False)
class ModelRequest:
    prompt: str
    system_prompt: str = ""
    context: Mapping[str, Any] = field(default_factory=dict)
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = 1_024
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1_024,
        metadata: Mapping[str, Any] | None = None,
        *,
        system: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        if system is not None and system_prompt and system != system_prompt:
            raise ValueError("system and system_prompt must not conflict")
        if context is not None and not isinstance(context, Mapping):
            raise TypeError("context must be a mapping")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        try:
            normalized_temperature = float(temperature)
        except (TypeError, ValueError) as exc:
            raise ValueError("temperature must be numeric") from exc
        if isinstance(max_tokens, bool):
            raise TypeError("max_tokens must be an integer")
        try:
            normalized_max_tokens = int(max_tokens)
        except (TypeError, ValueError) as exc:
            raise ValueError("max_tokens must be an integer") from exc
        object.__setattr__(self, "prompt", prompt)
        object.__setattr__(self, "system_prompt", system if system is not None else system_prompt)
        object.__setattr__(self, "context", MappingProxyType(dict(context or {})))
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "temperature", normalized_temperature)
        object.__setattr__(self, "max_tokens", normalized_max_tokens)
        object.__setattr__(self, "metadata", MappingProxyType(dict(metadata or {})))
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("model prompt must not be empty")
        if len(self.prompt) > 1_000_000:
            raise ValueError("model prompt exceeds 1,000,000 characters")
        if not isinstance(self.system_prompt, str):
            raise TypeError("system prompt must be a string")
        if len(self.system_prompt) > 200_000:
            raise ValueError("system prompt exceeds 200,000 characters")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")
        if not 1 <= self.max_tokens <= 1_000_000:
            raise ValueError("max_tokens must be between 1 and 1,000,000")

    @property
    def system(self) -> str:
        """Compatibility alias for subsystem adapters using ``system``."""

        return self.system_prompt

    @property
    def rendered_prompt(self) -> str:
        if not self.context:
            return self.prompt
        serialized = json.dumps(
            dict(self.context), sort_keys=True, separators=(",", ":"), default=str
        )
        return f"{self.prompt}\n\n[structured_context]\n{serialized}"

    @property
    def input_hash(self) -> str:
        payload = f"{self.system_prompt}\x00{self.rendered_prompt}".encode()
        return sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    finish_reason: str = "completed"
    usage: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("model response text must be a string")
        if not self.provider or not self.model:
            raise ValueError("provider and model must not be empty")
        object.__setattr__(self, "usage", MappingProxyType(dict(self.usage)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def output_hash(self) -> str:
        return sha256(self.text.encode("utf-8")).hexdigest()

    @property
    def content(self) -> str:
        """Compatibility alias for subsystem adapters using ``content``."""

        return self.text


@runtime_checkable
class ModelProvider(Protocol):
    name: str

    def generate(self, request: ModelRequest) -> ModelResponse: ...

    def stream(self, request: ModelRequest) -> Iterator[str]: ...


class ChunkedProvider:
    """Shared bounded chunking for adapters without native public streaming."""

    chunk_size: int = 80

    def stream(self, request: ModelRequest) -> Iterator[str]:
        text = self.generate(request).text
        yield from (
            text[start : start + self.chunk_size] for start in range(0, len(text), self.chunk_size)
        )
