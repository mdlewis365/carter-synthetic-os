# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Bounded public Semantic Adjudication Layer (SAL).

SAL validates and normalizes JSON returned across a probabilistic boundary. It
does not establish that model-generated statements are factually correct.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


def _reject_nonstandard_constant(token: str) -> None:
    raise ValueError(token)


@dataclass(frozen=True, slots=True)
class SALResult:
    valid: bool
    value: Mapping[str, Any] | None
    issues: tuple[str, ...] = ()
    normalized: bool = False


def _bounded(value: Any, *, depth: int, max_depth: int, max_items: int) -> Any:
    if depth > max_depth:
        raise ValueError("maximum JSON depth exceeded")
    if isinstance(value, Mapping):
        if len(value) > max_items:
            raise ValueError("maximum JSON object size exceeded")
        return {
            str(key): _bounded(item, depth=depth + 1, max_depth=max_depth, max_items=max_items)
            for key, item in value.items()
        }
    if isinstance(value, list):
        if len(value) > max_items:
            raise ValueError("maximum JSON array size exceeded")
        return [
            _bounded(item, depth=depth + 1, max_depth=max_depth, max_items=max_items)
            for item in value
        ]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite JSON number rejected")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def normalize_json(
    payload: str | bytes | Mapping[str, Any],
    *,
    required_fields: Iterable[str] = (),
    max_bytes: int = 256_000,
    max_depth: int = 20,
    max_items: int = 10_000,
) -> SALResult:
    """Parse one JSON object and apply bounded structural checks.

    The only text repair is removal of one outer Markdown JSON fence. SAL does
    not guess missing punctuation or silently extract an object from prose.
    """

    normalized = False
    if isinstance(payload, Mapping):
        value: Any = dict(payload)
    else:
        if isinstance(payload, bytes):
            if len(payload) > max_bytes:
                return SALResult(False, None, ("payload_size_limit_exceeded",))
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError:
                return SALResult(False, None, ("payload_not_utf8",))
        elif isinstance(payload, str):
            if len(payload.encode("utf-8")) > max_bytes:
                return SALResult(False, None, ("payload_size_limit_exceeded",))
            text = payload
        else:
            return SALResult(False, None, ("unsupported_payload_type",))
        fence_match = _FENCE.fullmatch(text)
        if fence_match:
            text = fence_match.group(1)
            normalized = True
        try:
            value = json.loads(text, parse_constant=_reject_nonstandard_constant)
        except (json.JSONDecodeError, ValueError):
            return SALResult(False, None, ("invalid_json",), normalized)

    if not isinstance(value, Mapping):
        return SALResult(False, None, ("root_must_be_object",), normalized)
    try:
        bounded = _bounded(value, depth=0, max_depth=max_depth, max_items=max_items)
    except ValueError as exc:
        return SALResult(False, None, (str(exc),), normalized)
    missing = tuple(sorted(str(field) for field in required_fields if str(field) not in bounded))
    if missing:
        return SALResult(
            False,
            bounded,
            tuple(f"missing_required_field:{field}" for field in missing),
            normalized,
        )
    return SALResult(True, bounded, normalized=normalized)


def normalize_interpretation(payload: str | bytes | Mapping[str, Any]) -> SALResult:
    """Normalize the common governed-interpretation envelope."""

    return normalize_json(payload, required_fields=("classification", "summary"))
