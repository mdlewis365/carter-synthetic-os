# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Provider registry and stable provider factory."""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from typing import Any

from .base import ModelProvider, ProviderError

ProviderFactory = Callable[..., ModelProvider]

_BUILTINS: dict[str, tuple[str, str]] = {
    "mock": ("sos.models.mock", "MockProvider"),
    "ollama": ("sos.models.ollama", "OllamaProvider"),
    "openai": ("sos.models.openai", "OpenAIProvider"),
    "anthropic": ("sos.models.anthropic", "AnthropicProvider"),
    "google": ("sos.models.google", "GoogleProvider"),
    "gemini": ("sos.models.google", "GoogleProvider"),
}


class ProviderRegistry:
    """Mutable application-level registry; it stores factories, not clients."""

    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}

    def register(self, name: str, factory: ProviderFactory) -> None:
        normalized = name.strip().casefold()
        if not normalized:
            raise ValueError("provider name must not be empty")
        if normalized in self._factories:
            raise ValueError(f"provider already registered: {normalized}")
        self._factories[normalized] = factory

    def create(
        self,
        name: str,
        *,
        model: str | None = None,
        settings: Mapping[str, Any] | None = None,
    ) -> ModelProvider:
        normalized = name.strip().casefold()
        try:
            factory = self._factories[normalized]
        except KeyError as exc:
            raise ProviderError(
                "Unknown model provider",
                provider="unknown",
                code="unknown_provider",
            ) from exc
        return factory(model=model, settings=settings)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))


def _load_builtin(name: str) -> ProviderFactory:
    module_name, class_name = _BUILTINS[name]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def available_providers() -> tuple[str, ...]:
    return tuple(sorted(_BUILTINS))


def create_provider(
    name: str,
    *,
    model: str | None = None,
    settings: Mapping[str, Any] | None = None,
) -> ModelProvider:
    """Create a provider adapter without initializing a network client."""

    normalized = str(name).strip().casefold()
    if normalized not in _BUILTINS:
        raise ProviderError(
            "Unknown model provider",
            provider="unknown",
            code="unknown_provider",
        )
    factory = _load_builtin(normalized)
    return factory(model=model, settings=settings)
