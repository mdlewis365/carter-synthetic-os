# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Governed interpretation of the rolling transcript buffer."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from sos.models import ModelRequest, ProviderError, create_provider

PRIORITIES = {"focused", "peripheral", "ignored", "background"}
UTTERANCE_TYPES = {"direct_address", "ambient_speech", "self_talk", "silence", "unclear"}
NEXT_STEPS = {
    "none",
    "prepare_candidate_response",
    "ask_for_clarification",
    "wait_for_more_speech",
}


def _reject_nonfinite_json_constant(constant: str) -> object:
    raise ValueError(f"nonfinite_json_constant:{constant}")


def _bool(value: object) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def _parse(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    text = re.sub(r"<think>.*?</think>", "", str(value or ""), flags=re.DOTALL)
    text = re.sub(r"^\x60{3}(?:json)?\s*|\s*\x60{3}$", "", text.strip())
    try:
        parsed = json.loads(text, parse_constant=_reject_nonfinite_json_constant)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("interpretation_not_json") from None
        parsed = json.loads(
            match.group(0),
            parse_constant=_reject_nonfinite_json_constant,
        )
    if not isinstance(parsed, dict):
        raise ValueError("interpretation_not_object")
    return parsed


def normalize_interpretation(
    value: object,
    *,
    buffer_context: dict[str, Any],
    backend: str,
) -> dict[str, object]:
    parsed = _parse(value)
    events = list(buffer_context.get("events") or [])
    latest = events[-1] if events else {}
    attention = str(latest.get("attention") or "background")
    if attention not in PRIORITIES:
        attention = "background"
    addressing = bool(latest.get("wake_name_detected")) and attention == "focused"

    semantic_complete = _optional_bool(parsed.get("semantic_complete"))
    utterance_type = str(parsed.get("utterance_type") or "unclear").lower()
    if utterance_type not in UTTERANCE_TYPES:
        utterance_type = "unclear"
    if addressing:
        utterance_type = "direct_address"

    priority = str(parsed.get("priority") or attention).lower()
    if priority not in PRIORITIES:
        priority = attention
    if priority == "focused" and not addressing:
        priority = attention

    next_step = str(parsed.get("recommended_next_step") or "none").lower()
    if next_step not in NEXT_STEPS:
        next_step = "none"
    candidate_needed = (
        addressing and semantic_complete is True and _bool(parsed.get("candidate_response_needed"))
    )
    if not candidate_needed and next_step == "prepare_candidate_response":
        next_step = "wait_for_more_speech" if addressing else "none"

    try:
        confidence_value = float(parsed.get("confidence", 0.0))
        if not math.isfinite(confidence_value):
            raise ValueError("confidence_not_finite")
        confidence = max(0.0, min(1.0, confidence_value))
    except (TypeError, ValueError):
        confidence = 0.0

    return {
        "interpretation_status": "interpreted",
        "addressing_carter": addressing,
        "semantic_complete": semantic_complete,
        "priority": priority,
        "utterance_type": utterance_type,
        "candidate_response_needed": candidate_needed,
        "recommended_next_step": next_step,
        "confidence": confidence,
        "reason": " ".join(str(parsed.get("reason") or "").split())[:280],
        "backend": backend,
        "governed": True,
        "authorizes_response": False,
        "authorizes_memory_write": False,
        "raw_audio_retained": False,
    }


def interpret_buffer(
    buffer_context: dict[str, Any],
    *,
    backend: str = "mock",
    model: str | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, object]:
    events = list(buffer_context.get("events") or [])
    if not events:
        return {
            "interpretation_status": "not_ready",
            "reason": "rolling transcript buffer is empty",
            "priority": "background",
            "backend": backend,
            "governed": True,
            "authorizes_response": False,
            "authorizes_memory_write": False,
        }
    latest = events[-1]
    if backend == "disabled":
        return {
            "interpretation_status": "skipped",
            "reason": "interpretation is disabled",
            "priority": latest.get("attention", "background"),
            "backend": "disabled",
            "governed": True,
            "authorizes_response": False,
            "authorizes_memory_write": False,
        }

    request = ModelRequest(
        prompt=(
            "Classify the supplied rolling transcript context. Return JSON only "
            "with semantic_complete, priority, utterance_type, "
            "candidate_response_needed, recommended_next_step, confidence, reason."
        ),
        system="csc_interpretation",
        context={"buffer": buffer_context},
        metadata={"mock_fixture": "csc_attention_v1"},
    )
    try:
        response = create_provider(backend, model=model, settings=settings or {}).generate(request)
        return normalize_interpretation(
            response.content,
            buffer_context=buffer_context,
            backend=response.provider,
        )
    except (ProviderError, ValueError, json.JSONDecodeError):
        return {
            "interpretation_status": "error",
            "reason": "interpretation_backend_error",
            "priority": latest.get("attention", "background"),
            "backend": backend,
            "governed": True,
            "authorizes_response": False,
            "authorizes_memory_write": False,
        }
