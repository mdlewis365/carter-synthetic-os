# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Deterministic computation boundary for Synthetic OS."""

from .mcm import process, summarize_run_health

__all__ = ["process", "summarize_run_health"]
