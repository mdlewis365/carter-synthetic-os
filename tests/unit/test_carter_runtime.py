# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Regression tests for Carter's cross-subsystem runtime boundary."""

from __future__ import annotations

import pytest

from carter.runtime import CarterRuntime
from shared.config import load_settings

pytestmark = pytest.mark.unit


def test_crm_context_preserves_turn_order_beyond_single_digits() -> None:
    runtime = CarterRuntime(load_settings({}))
    for index in range(12):
        runtime.crm.append("session", "user", f"turn-{index + 1:02d}")

    blocks = runtime._context_blocks("session", "current request")
    crm_contents = [block.content for block in blocks if block.source == "session_crm"]

    assert crm_contents == [f"turn-{index + 1:02d}" for index in range(12)]


def test_cloud_provider_does_not_inherit_ollama_endpoint() -> None:
    runtime = CarterRuntime(
        load_settings(
            {
                "CARTER_PROVIDER": "openai",
                "OPENAI_MODEL": "synthetic-model",
            }
        )
    )

    assert runtime.provider.name == "openai"
    assert runtime.provider.base_url is None
