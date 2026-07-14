# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Clearly labeled deterministic synthetic provider for offline demonstrations."""

from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256
from typing import Any

from .base import ChunkedProvider, ModelRequest, ModelResponse


class MockProvider(ChunkedProvider):
    """A fixture provider; it is explicitly not a language model."""

    name = "mock"

    def __init__(
        self,
        *,
        model: str | None = None,
        settings: Mapping[str, Any] | None = None,
    ) -> None:
        config = dict(settings or {})
        self.model = model or str(config.get("model") or "deterministic-mock-v1")
        self.fixtures = dict(config.get("fixtures") or {})
        self.default_response = config.get("default_response")
        self.chunk_size = int(config.get("chunk_size", 80))
        if self.chunk_size < 1:
            raise ValueError("mock chunk_size must be positive")

    def generate(self, request: ModelRequest) -> ModelResponse:
        fixture_input_hash = sha256(request.prompt.encode("utf-8")).hexdigest()
        fixture = self.fixtures.get(request.prompt)
        fixture_name = request.metadata.get("mock_fixture")
        if fixture is None and fixture_name == "csc_attention_v1":
            fixture = json.dumps(
                {
                    "semantic_complete": True,
                    "priority": "focused",
                    "utterance_type": "direct_address",
                    "candidate_response_needed": True,
                    "recommended_next_step": "prepare_candidate_response",
                    "confidence": 1.0,
                    "reason": "deterministic synthetic CSC fixture",
                },
                sort_keys=True,
            )
        if fixture is None:
            fixture = self.default_response
        if fixture is None:
            fixture = (
                "[Mock provider: deterministic synthetic output]\n"
                "The governed request pipeline completed without invoking a language model.\n"
                f"Input fingerprint: {fixture_input_hash[:16]}"
            )
        return ModelResponse(
            text=str(fixture),
            provider=self.name,
            model=request.model or self.model,
            metadata={
                "synthetic": True,
                "deterministic": True,
                "language_model_invoked": False,
                "input_hash": request.input_hash,
                "fixture_input_hash": fixture_input_hash,
            },
        )
