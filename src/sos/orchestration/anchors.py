# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Explicit temporal and session-context anchors."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True, slots=True)
class TemporalAnchor:
    captured_at_utc: str
    local_time: str
    timezone_name: str

    def render(self) -> str:
        return f"Time anchor: {self.local_time} ({self.timezone_name}); UTC {self.captured_at_utc}."


@dataclass(frozen=True, slots=True)
class ContextAnchor:
    session_hash: str
    turn_index: int | None = None
    labels: tuple[str, ...] = ()

    def render(self) -> str:
        parts = [f"Session anchor: {self.session_hash}"]
        if self.turn_index is not None:
            parts.append(f"turn {self.turn_index}")
        if self.labels:
            parts.append("labels " + ", ".join(self.labels))
        return "; ".join(parts) + "."


def temporal_anchor(*, now: datetime | None = None, timezone_name: str = "UTC") -> TemporalAnchor:
    """Create an explicit, timezone-aware clock anchor."""

    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        raise ValueError("now must include timezone information")
    try:
        local_zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {timezone_name}") from exc
    utc_moment = moment.astimezone(UTC)
    local_moment = moment.astimezone(local_zone)
    return TemporalAnchor(
        captured_at_utc=utc_moment.isoformat().replace("+00:00", "Z"),
        local_time=local_moment.isoformat(),
        timezone_name=timezone_name,
    )


def context_anchor(
    session_id: str,
    *,
    turn_index: int | None = None,
    labels: Iterable[str] = (),
) -> ContextAnchor:
    """Create a non-reversible session anchor suitable for reports and logs."""

    if not session_id:
        raise ValueError("session_id must not be empty")
    if turn_index is not None and turn_index < 0:
        raise ValueError("turn_index must not be negative")
    normalized_labels = tuple(
        sorted({str(label).strip() for label in labels if str(label).strip()})
    )
    return ContextAnchor(
        session_hash=sha256(session_id.encode("utf-8")).hexdigest()[:16],
        turn_index=turn_index,
        labels=normalized_labels,
    )
