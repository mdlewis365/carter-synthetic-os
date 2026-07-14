# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Provider-neutral orchestration contracts and pipeline helpers."""

from .anchors import ContextAnchor, TemporalAnchor, context_anchor, temporal_anchor
from .context import ContextAssembly, ContextBlock, assemble_context
from .contracts import NormalizedRequest, PipelineResult, normalize_request
from .pipeline import run_pipeline

__all__ = [
    "ContextAnchor",
    "ContextAssembly",
    "ContextBlock",
    "NormalizedRequest",
    "PipelineResult",
    "TemporalAnchor",
    "assemble_context",
    "context_anchor",
    "normalize_request",
    "run_pipeline",
    "temporal_anchor",
]
