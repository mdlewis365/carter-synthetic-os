# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Disabled-by-default ChromaDB memory adapter boundary.

No Chroma client, persistence directory, embedding model, or collection is
created until an explicitly enabled adapter receives an operation. Release
0.1.0 does not declare a ChromaDB dependency because all current 1.x releases
are affected by CVE-2026-45829.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from threading import RLock
from typing import Any

from .base import MemoryDisabledError, MemoryRecord


class ChromaMemoryStore:
    def __init__(
        self,
        *,
        collection_name: str = "carter_public_memory",
        persist_directory: str | Path | None = None,
        enabled: bool = False,
    ) -> None:
        if not collection_name.strip():
            raise ValueError("collection_name must not be empty")
        self.collection_name = collection_name
        self.persist_directory = str(persist_directory) if persist_directory is not None else None
        self.enabled = enabled
        self._client: Any = None
        self._collection: Any = None
        self._lock = RLock()

    @property
    def persistent(self) -> bool:
        return self.persist_directory is not None

    def _get_collection(self) -> Any:
        if not self.enabled:
            raise MemoryDisabledError(
                "Chroma memory is disabled; pass enabled=True only after obtaining consent"
            )
        with self._lock:
            if self._collection is None:
                try:
                    chromadb = importlib.import_module("chromadb")
                except ImportError as exc:
                    raise RuntimeError(
                        "ChromaDB is not installed by this release because the current "
                        "dependency line is blocked by CVE-2026-45829"
                    ) from exc
                if self.persist_directory is None:
                    self._client = chromadb.EphemeralClient()
                else:
                    self._client = chromadb.PersistentClient(path=self.persist_directory)
                self._collection = self._client.get_or_create_collection(self.collection_name)
            return self._collection

    def put(self, record: MemoryRecord) -> MemoryRecord:
        self._get_collection().upsert(
            ids=[record.record_id],
            documents=[record.content],
            metadatas=[
                {
                    "session_id": record.session_id,
                    "created_at": record.created_at,
                    "metadata_json": json.dumps(dict(record.metadata), sort_keys=True),
                }
            ],
        )
        return record

    def list(self, session_id: str, *, limit: int = 100) -> tuple[MemoryRecord, ...]:
        if limit < 0:
            raise ValueError("limit must not be negative")
        if limit == 0:
            return ()
        result = self._get_collection().get(
            where={"session_id": session_id},
            limit=limit,
            include=["documents", "metadatas"],
        )
        ids = result.get("ids") or []
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []
        records = [
            MemoryRecord(
                record_id=record_id,
                session_id=metadata["session_id"],
                content=document,
                created_at=metadata["created_at"],
                metadata=json.loads(metadata.get("metadata_json") or "{}"),
            )
            for record_id, document, metadata in zip(ids, documents, metadatas, strict=True)
        ]
        records.sort(key=lambda record: (record.created_at, record.record_id))
        return tuple(records)

    def clear(self, session_id: str) -> int:
        collection = self._get_collection()
        result = collection.get(where={"session_id": session_id})
        ids = result.get("ids") or []
        if ids:
            collection.delete(ids=ids)
        return len(ids)
