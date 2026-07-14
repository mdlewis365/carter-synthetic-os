# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Redacted, in-memory lifecycle events."""

from __future__ import annotations

import json
import re
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import uuid4

_SENSITIVE_KEY = re.compile(
    r"(?:prompt|input|output|content|message|conversation|secret|password|token|"
    r"api.?key|authorization|cookie|email|phone|voice.?id|account)",
    re.IGNORECASE,
)
_SAFE_HASH = re.compile(r"^[0-9a-f]{32,128}$")


def _safe_value(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return "[TRUNCATED]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:500]
    if isinstance(value, Mapping):
        return sanitize_metadata(value, _depth=depth + 1)
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_safe_value(item, depth + 1) for item in list(value)[:100]]
    return f"<{type(value).__name__}>"


def sanitize_metadata(metadata: Mapping[str, Any], *, _depth: int = 0) -> dict[str, Any]:
    """Redact content-bearing keys and bound metadata for safe observability."""

    result: dict[str, Any] = {}
    for raw_key, value in list(metadata.items())[:100]:
        key = str(raw_key)[:100]
        is_safe_hash = key.endswith("_hash") and _SAFE_HASH.fullmatch(str(value))
        if _SENSITIVE_KEY.search(key) and not is_safe_hash:
            result[key] = "[REDACTED]"
        else:
            result[key] = _safe_value(value, _depth)
    return result


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    event_id: str
    event_type: str
    occurred_at: str
    request_id: str | None
    session_hash: str | None
    status: str
    metadata: Mapping[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))


class EventRecorder:
    """Bounded process-local event sink with no persistence side effects."""

    def __init__(
        self,
        *,
        capacity: int = 1_000,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._events: deque[LifecycleEvent] = deque(maxlen=capacity)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: uuid4().hex)

    def record(
        self,
        event_type: str,
        *,
        request_id: str | None = None,
        session_id: str | None = None,
        status: str = "ok",
        metadata: Mapping[str, Any] | None = None,
    ) -> LifecycleEvent:
        if not event_type or len(event_type) > 100:
            raise ValueError("event_type must contain between 1 and 100 characters")
        moment = self._clock()
        if moment.tzinfo is None:
            raise ValueError("event clock must return a timezone-aware datetime")
        event = LifecycleEvent(
            event_id=self._id_factory(),
            event_type=event_type,
            occurred_at=moment.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            request_id=request_id,
            session_hash=(
                sha256(session_id.encode("utf-8")).hexdigest()[:16] if session_id else None
            ),
            status=str(status)[:100],
            metadata=sanitize_metadata(metadata or {}),
        )
        self._events.append(event)
        return event

    def snapshot(self) -> tuple[LifecycleEvent, ...]:
        return tuple(self._events)

    def clear(self) -> None:
        self._events.clear()
