# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Session-scoped rolling Contextual/Conversation Memory (CRM)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

from .base import MemoryRecord, new_memory_record

_ROLES = frozenset({"user", "assistant", "system", "tool"})


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    role: str
    content: str
    created_at: str


class RollingContextMemory:
    """Bounded turn buffer isolated by session and retained only in memory."""

    def __init__(
        self,
        *,
        max_turns: int = 20,
        ttl_seconds: int = 3600,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if max_turns < 1 or ttl_seconds < 1:
            raise ValueError("max_turns and ttl_seconds must be positive")
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._sessions: dict[str, deque[ConversationTurn]] = defaultdict(
            lambda: deque(maxlen=max_turns)
        )
        self._last_seen: dict[str, float] = {}
        self._lock = RLock()

    def _prune_locked(self, now: float) -> None:
        cutoff = now - self.ttl_seconds
        for session_id, last_seen in list(self._last_seen.items()):
            if last_seen < cutoff:
                self._sessions.pop(session_id, None)
                self._last_seen.pop(session_id, None)

    @property
    def persistent(self) -> bool:
        return False

    def append(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        created_at: datetime | None = None,
    ) -> ConversationTurn:
        session = str(session_id).strip()
        normalized_role = str(role).strip().casefold()
        if not session:
            raise ValueError("session_id must not be empty")
        if normalized_role not in _ROLES:
            raise ValueError(f"unsupported conversation role: {role}")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("turn content must not be empty")
        moment = created_at or datetime.now(UTC)
        if moment.tzinfo is None:
            raise ValueError("created_at must include timezone information")
        turn = ConversationTurn(
            role=normalized_role,
            content=content.strip(),
            created_at=moment.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        )
        with self._lock:
            now = self._clock()
            self._prune_locked(now)
            self._sessions[session].append(turn)
            self._last_seen[session] = now
        return turn

    def extend(self, session_id: str, turns: Iterable[tuple[str, str]]) -> None:
        for role, content in turns:
            self.append(session_id, role, content)

    def recent(self, session_id: str, *, limit: int | None = None) -> tuple[ConversationTurn, ...]:
        if limit is not None and limit < 0:
            raise ValueError("limit must not be negative")
        with self._lock:
            now = self._clock()
            self._prune_locked(now)
            turns = tuple(self._sessions.get(session_id, ()))
            if turns:
                self._last_seen[session_id] = now
        return turns if limit is None else (turns[-limit:] if limit else ())

    def as_records(self, session_id: str) -> tuple[MemoryRecord, ...]:
        return tuple(
            new_memory_record(
                session_id,
                turn.content,
                metadata={"role": turn.role, "memory_type": "crm"},
                created_at=datetime.fromisoformat(turn.created_at.replace("Z", "+00:00")),
            )
            for turn in self.recent(session_id)
        )

    def clear(self, session_id: str) -> int:
        with self._lock:
            self._last_seen.pop(session_id, None)
            return len(self._sessions.pop(session_id, ()))
