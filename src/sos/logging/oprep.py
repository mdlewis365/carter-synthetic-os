# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Metadata-only operational reporting (OpRep)."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256

from .events import LifecycleEvent


@dataclass(frozen=True, slots=True)
class OperationReport:
    report_id: str
    generated_at: str
    event_count: int
    event_types: Mapping[str, int]
    statuses: Mapping[str, int]
    first_event_at: str | None
    last_event_at: str | None
    artifact_hashes: Mapping[str, str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, indent=2)


def build_operation_report(
    events: Iterable[LifecycleEvent],
    *,
    artifact_hashes: Mapping[str, str] | None = None,
    generated_at: datetime | None = None,
) -> OperationReport:
    """Summarize lifecycle metadata without copying any model content."""

    records = tuple(events)
    hashes = dict(artifact_hashes or {})
    for name, digest in hashes.items():
        if not name or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("artifact hashes must be named SHA-256 hex digests")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ValueError("artifact hashes must be named SHA-256 hex digests") from exc
    timestamp = generated_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        raise ValueError("generated_at must include timezone information")
    identity_payload = (
        "|".join(event.event_id for event in records)
        + "|"
        + "|".join(f"{name}:{hashes[name]}" for name in sorted(hashes))
    )
    return OperationReport(
        report_id=sha256(identity_payload.encode("utf-8")).hexdigest()[:24],
        generated_at=timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        event_count=len(records),
        event_types=dict(Counter(event.event_type for event in records)),
        statuses=dict(Counter(event.status for event in records)),
        first_event_at=records[0].occurred_at if records else None,
        last_event_at=records[-1].occurred_at if records else None,
        artifact_hashes=hashes,
    )
