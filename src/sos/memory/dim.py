# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Deterministic Data Ingestion Module (DIM) with exact deduplication."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Any

from .base import MemoryRecord, MemoryStore, new_memory_record

_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class SourceDocument:
    content: str
    source_id: str = "caller"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class IngestionDecision:
    source_id: str
    content_hash: str
    accepted: bool
    reason: str
    record_id: str | None = None


@dataclass(frozen=True, slots=True)
class IngestionBatch:
    namespace: str
    decisions: tuple[IngestionDecision, ...]

    @property
    def accepted_count(self) -> int:
        return sum(decision.accepted for decision in self.decisions)

    @property
    def duplicate_count(self) -> int:
        return sum(not decision.accepted for decision in self.decisions)


def canonicalize_content(content: str) -> str:
    if not isinstance(content, str):
        raise TypeError("document content must be a string")
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFKC", content)).strip()


class DIMIngestor:
    """Normalize and deduplicate documents without probabilistic processing."""

    def __init__(self, *, known_hashes: Iterable[str] = ()) -> None:
        self._known: set[tuple[str, str, str]] = set()
        for digest in known_hashes:
            normalized = str(digest).casefold()
            if len(normalized) != 64:
                raise ValueError("known hashes must be SHA-256 hex digests")
            try:
                int(normalized, 16)
            except ValueError as exc:
                raise ValueError("known hashes must be SHA-256 hex digests") from exc
            self._known.add(("*", "default", normalized))

    def ingest(
        self,
        documents: Iterable[SourceDocument | str | Mapping[str, Any]],
        *,
        session_id: str,
        namespace: str = "default",
        store: MemoryStore | None = None,
    ) -> IngestionBatch:
        if not session_id.strip() or not namespace.strip():
            raise ValueError("session_id and namespace must not be empty")
        decisions: list[IngestionDecision] = []
        for index, value in enumerate(documents):
            if isinstance(value, SourceDocument):
                document = value
            elif isinstance(value, str):
                document = SourceDocument(value, source_id=f"item-{index}")
            elif isinstance(value, Mapping):
                document = SourceDocument(
                    content=str(value.get("content") or ""),
                    source_id=str(value.get("source_id") or f"item-{index}"),
                    metadata=value.get("metadata") or {},
                )
            else:
                raise TypeError("documents must contain SourceDocument, string, or mapping values")
            canonical = canonicalize_content(document.content)
            if not canonical:
                decisions.append(
                    IngestionDecision(
                        document.source_id,
                        sha256(b"").hexdigest(),
                        False,
                        "empty",
                    )
                )
                continue
            digest = sha256(canonical.casefold().encode("utf-8")).hexdigest()
            key = (session_id, namespace, digest)
            if key in self._known or ("*", namespace, digest) in self._known:
                decisions.append(IngestionDecision(document.source_id, digest, False, "duplicate"))
                continue
            record: MemoryRecord | None = None
            if store is not None:
                record = store.put(
                    new_memory_record(
                        session_id,
                        canonical,
                        metadata={
                            **dict(document.metadata),
                            "source_id": document.source_id,
                            "content_hash": digest,
                            "namespace": namespace,
                        },
                    )
                )
            self._known.add(key)
            decisions.append(
                IngestionDecision(
                    document.source_id,
                    digest,
                    True,
                    "accepted",
                    record.record_id if record else None,
                )
            )
        return IngestionBatch(namespace, tuple(decisions))

    def contains(self, content: str, *, session_id: str, namespace: str = "default") -> bool:
        if not session_id.strip() or not namespace.strip():
            raise ValueError("session_id and namespace must not be empty")
        canonical = canonicalize_content(content)
        digest = sha256(canonical.casefold().encode("utf-8")).hexdigest()
        return (session_id, namespace, digest) in self._known or (
            "*",
            namespace,
            digest,
        ) in self._known
