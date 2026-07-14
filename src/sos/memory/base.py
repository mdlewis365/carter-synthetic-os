# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Common memory records and storage protocol."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable
from uuid import uuid4


class MemoryDisabledError(RuntimeError):
    """Raised when an operator has not explicitly enabled persistence."""


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    record_id: str
    session_id: str
    content: str
    created_at: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.record_id.strip() or not self.session_id.strip():
            raise ValueError("record_id and session_id must not be empty")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("memory content must not be empty")
        try:
            timestamp = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("created_at must be an ISO-8601 timestamp") from exc
        if timestamp.tzinfo is None:
            raise ValueError("created_at must include timezone information")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def new_memory_record(
    session_id: str,
    content: str,
    *,
    metadata: Mapping[str, Any] | None = None,
    record_id: str | None = None,
    created_at: datetime | None = None,
) -> MemoryRecord:
    moment = created_at or datetime.now(UTC)
    if moment.tzinfo is None:
        raise ValueError("created_at must include timezone information")
    return MemoryRecord(
        record_id=record_id or uuid4().hex,
        session_id=str(session_id).strip(),
        content=content,
        created_at=moment.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        metadata=metadata or {},
    )


@runtime_checkable
class MemoryStore(Protocol):
    """Minimal session-aware memory storage boundary."""

    @property
    def persistent(self) -> bool: ...

    def put(self, record: MemoryRecord) -> MemoryRecord: ...

    def list(self, session_id: str, *, limit: int = 100) -> tuple[MemoryRecord, ...]: ...

    def clear(self, session_id: str) -> int: ...
