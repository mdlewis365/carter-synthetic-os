# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""A compact governed request pipeline used by the public demonstration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from sos.governance import GovernanceGate, GovernanceStatus
from sos.logging import EventRecorder
from sos.models import ModelProvider, ModelRequest, ProviderError, create_provider

from .context import ContextBlock, assemble_context
from .contracts import NormalizedRequest, PipelineResult, normalize_request


def run_pipeline(
    value: str | Mapping[str, Any] | NormalizedRequest,
    *,
    provider: ModelProvider | None = None,
    context_blocks: Iterable[ContextBlock | str | Mapping[str, Any]] = (),
    anchors: Iterable[Any] = (),
    governance: GovernanceGate | None = None,
    recorder: EventRecorder | None = None,
    model: str | None = None,
) -> PipelineResult:
    """Normalize, govern, assemble, invoke, and record one request.

    Event records contain hashes and bounded metadata, never prompt or response
    text. The deterministic mock provider is used only when explicitly omitted.
    """

    normalized = normalize_request(value)
    gate = governance if governance is not None else GovernanceGate()
    decision = gate.evaluate_request(normalized.text)
    context = assemble_context(normalized, blocks=context_blocks, anchors=anchors)
    sink = recorder if recorder is not None else EventRecorder()
    accepted = sink.record(
        "request.adjudicated",
        request_id=normalized.request_id,
        session_id=normalized.session_id,
        status=decision.status.value,
        metadata={
            "input_hash": normalized.input_hash,
            "context_truncated": context.truncated,
        },
    )
    if decision.status is GovernanceStatus.BLOCK:
        return PipelineResult(normalized, context, decision, None, (accepted.event_id,))

    selected_provider = provider if provider is not None else create_provider("mock", model=model)
    try:
        model_response = selected_provider.generate(
            ModelRequest(
                prompt=normalized.text,
                system_prompt=context.render(include_request=False),
                model=model,
                metadata={"request_id": normalized.request_id},
            )
        )
    except ProviderError as exc:
        sink.record(
            "provider.failed",
            request_id=normalized.request_id,
            session_id=normalized.session_id,
            status=exc.code,
            metadata={"provider": exc.provider, "retryable": exc.retryable},
        )
        raise
    completed = sink.record(
        "provider.completed",
        request_id=normalized.request_id,
        session_id=normalized.session_id,
        status="completed",
        metadata={
            "provider": model_response.provider,
            "model": model_response.model,
            "output_hash": model_response.output_hash,
        },
    )
    return PipelineResult(
        normalized,
        context,
        decision,
        model_response,
        (accepted.event_id, completed.event_id),
    )
