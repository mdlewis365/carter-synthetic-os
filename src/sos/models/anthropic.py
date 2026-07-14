# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Lazy optional Anthropic provider adapter."""

from __future__ import annotations

import importlib
import os
from collections.abc import Mapping
from typing import Any

from .base import ChunkedProvider, ModelRequest, ModelResponse, ProviderError


class AnthropicProvider(ChunkedProvider):
    name = "anthropic"

    def __init__(
        self,
        *,
        model: str | None = None,
        settings: Mapping[str, Any] | None = None,
    ) -> None:
        config = dict(settings or {})
        self.model = model or str(config.get("model") or "") or None
        self.api_key = config.get("api_key")

    def generate(self, request: ModelRequest) -> ModelResponse:
        model = request.model or self.model or os.environ.get("CARTER_DEFAULT_MODEL")
        api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderError(
                "ANTHROPIC_API_KEY is not configured",
                provider=self.name,
                code="missing_api_key",
            )
        if not model:
            raise ProviderError(
                "No Anthropic model is configured",
                provider=self.name,
                code="model_not_configured",
            )
        try:
            module = importlib.import_module("anthropic")
        except ImportError as exc:
            raise ProviderError(
                "Anthropic support is optional; install carter-synthetic-os[anthropic]",
                provider=self.name,
                code="missing_dependency",
            ) from exc
        try:
            client = module.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                system=request.system_prompt,
                messages=[{"role": "user", "content": request.rendered_prompt}],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            text_blocks = (
                block for block in response.content if getattr(block, "type", None) == "text"
            )
            text = "".join(str(block.text) for block in text_blocks)
            usage_object = getattr(response, "usage", None)
            usage = {
                "input_tokens": int(getattr(usage_object, "input_tokens", 0) or 0),
                "output_tokens": int(getattr(usage_object, "output_tokens", 0) or 0),
            }
        except Exception as exc:
            raise ProviderError(
                "Anthropic generation failed",
                provider=self.name,
                code="generation_failed",
                retryable=True,
            ) from exc
        return ModelResponse(text, self.name, model, usage=usage)
