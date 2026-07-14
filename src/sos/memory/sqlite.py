# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Explicitly enabled SQLite memory adapter."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any

from .base import MemoryDisabledError, MemoryRecord


class SQLiteMemoryStore:
    """Session-aware SQLite storage that is lazy and disabled by default."""

    def __init__(self, path: str | Path, *, enabled: bool = False) -> None:
        raw_path = str(path)
        if not raw_path.strip():
            raise ValueError("SQLite path must not be empty")
        self.path = raw_path if raw_path == ":memory:" else str(Path(raw_path).expanduser())
        self.enabled = enabled
        self._connection: sqlite3.Connection | None = None
        self._lock = RLock()

    @property
    def persistent(self) -> bool:
        return self.path != ":memory:"

    def _connect(self) -> sqlite3.Connection:
        if not self.enabled:
            raise MemoryDisabledError(
                "SQLite memory is disabled; pass enabled=True only after obtaining consent"
            )
        with self._lock:
            if self._connection is None:
                if self.path != ":memory:":
                    Path(self.path).expanduser().parent.mkdir(parents=True, exist_ok=True)
                connection = sqlite3.connect(self.path, check_same_thread=False)
                connection.row_factory = sqlite3.Row
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_records (
                        record_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        metadata_json TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memory_session_time "
                    "ON memory_records(session_id, created_at)"
                )
                connection.commit()
                self._connection = connection
            return self._connection

    def put(self, record: MemoryRecord) -> MemoryRecord:
        metadata_json = json.dumps(dict(record.metadata), sort_keys=True, separators=(",", ":"))
        with self._lock:
            connection = self._connect()
            try:
                connection.execute(
                    "INSERT INTO memory_records VALUES (?, ?, ?, ?, ?)",
                    (
                        record.record_id,
                        record.session_id,
                        record.content,
                        record.created_at,
                        metadata_json,
                    ),
                )
                connection.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"duplicate memory record id: {record.record_id}") from exc
        return record

    def list(self, session_id: str, *, limit: int = 100) -> tuple[MemoryRecord, ...]:
        if limit < 0:
            raise ValueError("limit must not be negative")
        if limit == 0:
            return ()
        with self._lock:
            rows = (
                self._connect()
                .execute(
                    "SELECT * FROM memory_records WHERE session_id = ? "
                    "ORDER BY created_at DESC, rowid DESC LIMIT ?",
                    (session_id, limit),
                )
                .fetchall()
            )
        return tuple(
            MemoryRecord(
                record_id=row["record_id"],
                session_id=row["session_id"],
                content=row["content"],
                created_at=row["created_at"],
                metadata=json.loads(row["metadata_json"]),
            )
            for row in reversed(rows)
        )

    def clear(self, session_id: str) -> int:
        with self._lock:
            connection = self._connect()
            cursor = connection.execute(
                "DELETE FROM memory_records WHERE session_id = ?", (session_id,)
            )
            connection.commit()
            return int(cursor.rowcount)

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def __enter__(self) -> SQLiteMemoryStore:
        self._connect()
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()
