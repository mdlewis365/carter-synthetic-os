# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Process-local Associative Memory System (AMS)."""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from collections.abc import Callable, Mapping
from threading import RLock
from typing import Any

from .base import MemoryRecord, new_memory_record

_WORD = re.compile(r"[A-Za-z0-9_]+")


class InMemoryAMS:
    """Bounded associative memory that never persists across process exit."""

    def __init__(
        self,
        *,
        capacity_per_session: int = 1_000,
        ttl_seconds: int = 3600,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if capacity_per_session < 1 or ttl_seconds < 1:
            raise ValueError("capacity_per_session and ttl_seconds must be positive")
        self.capacity_per_session = capacity_per_session
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._records: dict[str, deque[MemoryRecord]] = defaultdict(
            lambda: deque(maxlen=capacity_per_session)
        )
        self._last_seen: dict[str, float] = {}
        self._lock = RLock()

    def _prune_locked(self, now: float) -> None:
        cutoff = now - self.ttl_seconds
        for session_id, last_seen in list(self._last_seen.items()):
            if last_seen < cutoff:
                self._records.pop(session_id, None)
                self._last_seen.pop(session_id, None)

    @property
    def persistent(self) -> bool:
        return False

    def add(
        self,
        session_id: str,
        content: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> MemoryRecord:
        return self.put(new_memory_record(session_id, content, metadata=metadata))

    def put(self, record: MemoryRecord) -> MemoryRecord:
        with self._lock:
            now = self._clock()
            self._prune_locked(now)
            records = self._records[record.session_id]
            if any(existing.record_id == record.record_id for existing in records):
                raise ValueError(f"duplicate memory record id: {record.record_id}")
            records.append(record)
            self._last_seen[record.session_id] = now
        return record

    def list(self, session_id: str, *, limit: int = 100) -> tuple[MemoryRecord, ...]:
        if limit < 0:
            raise ValueError("limit must not be negative")
        with self._lock:
            now = self._clock()
            self._prune_locked(now)
            records = tuple(self._records.get(session_id, ()))
            if records:
                self._last_seen[session_id] = now
        return records[-limit:] if limit else ()

    def recall(
        self,
        session_id: str,
        query: str,
        *,
        limit: int = 5,
    ) -> tuple[MemoryRecord, ...]:
        """Rank records by deterministic token overlap, then recency."""

        if limit < 0:
            raise ValueError("limit must not be negative")
        query_tokens = frozenset(token.casefold() for token in _WORD.findall(query))
        if not query_tokens or limit == 0:
            return ()
        records = self.list(session_id, limit=self.capacity_per_session)
        ranked: list[tuple[float, int, MemoryRecord]] = []
        for index, record in enumerate(records):
            tokens = frozenset(token.casefold() for token in _WORD.findall(record.content))
            overlap = len(query_tokens.intersection(tokens))
            if overlap:
                score = overlap / len(query_tokens.union(tokens))
                ranked.append((score, index, record))
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return tuple(item[2] for item in ranked[:limit])

    def clear(self, session_id: str) -> int:
        with self._lock:
            self._last_seen.pop(session_id, None)
            records = self._records.pop(session_id, ())
            return len(records)

    def clear_all(self) -> int:
        with self._lock:
            count = sum(len(records) for records in self._records.values())
            self._records.clear()
            self._last_seen.clear()
            return count
