# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Lazy optional Google Gemini provider adapter."""

from __future__ import annotations

import importlib
import os
from collections.abc import Mapping
from typing import Any

from .base import ChunkedProvider, ModelRequest, ModelResponse, ProviderError


class GoogleProvider(ChunkedProvider):
    name = "google"

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
        api_key = self.api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderError(
                "GOOGLE_API_KEY is not configured",
                provider=self.name,
                code="missing_api_key",
            )
        if not model:
            raise ProviderError(
                "No Google model is configured",
                provider=self.name,
                code="model_not_configured",
            )
        try:
            module = importlib.import_module("google.genai")
            types = importlib.import_module("google.genai.types")
        except ImportError as exc:
            raise ProviderError(
                "Google support is optional; install carter-synthetic-os[google]",
                provider=self.name,
                code="missing_dependency",
            ) from exc
        try:
            client = module.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                system_instruction=request.system_prompt or None,
                max_output_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            response = client.models.generate_content(
                model=model,
                contents=request.rendered_prompt,
                config=config,
            )
            text = response.text
        except Exception as exc:
            raise ProviderError(
                "Google generation failed",
                provider=self.name,
                code="generation_failed",
                retryable=True,
            ) from exc
        return ModelResponse(str(text), self.name, model)
