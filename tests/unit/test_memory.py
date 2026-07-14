# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from sos.memory import (
    ChromaMemoryStore,
    DIMIngestor,
    InMemoryAMS,
    MemoryDisabledError,
    RollingContextMemory,
    SQLiteMemoryStore,
    new_memory_record,
)

pytestmark = pytest.mark.unit


def test_in_memory_ams_is_bounded_session_scoped_and_ephemeral() -> None:
    memory = InMemoryAMS(capacity_per_session=2)
    memory.add("session-a", "first synthetic note")
    memory.add("session-a", "second pump note")
    memory.add("session-a", "third pump note")
    memory.add("session-b", "private to the other synthetic session")

    assert memory.persistent is False
    assert [record.content for record in memory.list("session-a")] == [
        "second pump note",
        "third pump note",
    ]
    assert [record.content for record in memory.list("session-b")] == [
        "private to the other synthetic session"
    ]
    assert memory.recall("session-a", "pump", limit=1)[0].content == "third pump note"


def test_rolling_context_memory_discards_old_turns_and_clears_one_session() -> None:
    memory = RollingContextMemory(max_turns=2)
    memory.append("a", "user", "one")
    memory.append("a", "assistant", "two")
    memory.append("a", "user", "three")
    memory.append("b", "user", "isolated")

    assert [(turn.role, turn.content) for turn in memory.recent("a")] == [
        ("assistant", "two"),
        ("user", "three"),
    ]
    assert memory.clear("a") == 2
    assert memory.recent("a") == ()
    assert memory.recent("b")[0].content == "isolated"


def test_crm_and_ams_expire_idle_session_data() -> None:
    now = [100.0]

    def clock() -> float:
        return now[0]

    crm = RollingContextMemory(ttl_seconds=10, clock=clock)
    ams = InMemoryAMS(ttl_seconds=10, clock=clock)
    crm.append("session", "user", "synthetic turn")
    ams.add("session", "synthetic memory")
    now[0] += 11

    assert crm.recent("session") == ()
    assert ams.list("session") == ()


def test_dim_normalizes_and_deduplicates_exact_content() -> None:
    store = InMemoryAMS()
    ingestor = DIMIngestor()

    batch = ingestor.ingest(
        ["  Pump\ncurve  point ", "pump curve point", "different point"],
        session_id="synthetic-session",
        store=store,
    )

    assert batch.accepted_count == 2
    assert batch.duplicate_count == 1
    assert [decision.reason for decision in batch.decisions] == [
        "accepted",
        "duplicate",
        "accepted",
    ]
    assert len(store.list("synthetic-session")) == 2
    assert ingestor.contains("PUMP   CURVE POINT", session_id="synthetic-session") is True


def test_dim_namespaces_have_independent_deduplication() -> None:
    ingestor = DIMIngestor()
    first = ingestor.ingest(["same"], session_id="s", namespace="one")
    second = ingestor.ingest(["same"], session_id="s", namespace="two")

    assert first.accepted_count == second.accepted_count == 1


def test_dim_sessions_have_independent_deduplication() -> None:
    ingestor = DIMIngestor()
    first = ingestor.ingest(["same"], session_id="first")
    second = ingestor.ingest(["same"], session_id="second")

    assert first.accepted_count == second.accepted_count == 1


def test_dim_does_not_mark_content_known_when_storage_fails() -> None:
    class FailingStore:
        persistent = False

        def put(self, _record):
            raise RuntimeError("synthetic storage failure")

    ingestor = DIMIngestor()

    with pytest.raises(RuntimeError, match="synthetic storage failure"):
        ingestor.ingest(
            ["retryable synthetic document"],
            session_id="session",
            store=FailingStore(),
        )

    assert ingestor.contains("retryable synthetic document", session_id="session") is False


def test_sqlite_is_disabled_and_does_not_create_a_file_by_default(tmp_path) -> None:
    database_path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(database_path)

    with pytest.raises(MemoryDisabledError):
        store.list("session")

    assert not database_path.exists()


def test_sqlite_rejects_empty_path() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        SQLiteMemoryStore("   ")


def test_sqlite_persistence_requires_opt_in_and_preserves_session_isolation(tmp_path) -> None:
    database_path = tmp_path / "memory.sqlite3"
    record = new_memory_record("session-a", "synthetic persisted record", record_id="record-a")
    with SQLiteMemoryStore(database_path, enabled=True) as store:
        store.put(record)
        store.put(new_memory_record("session-b", "other", record_id="record-b"))

    with SQLiteMemoryStore(database_path, enabled=True) as reopened:
        assert reopened.list("session-a") == (record,)
        assert reopened.list("missing") == ()
        assert reopened.clear("session-a") == 1


def test_chroma_is_lazy_and_disabled_by_default() -> None:
    store = ChromaMemoryStore()

    assert store.persistent is False
    assert store._client is None
    with pytest.raises(MemoryDisabledError):
        store.list("session")


def test_chroma_dependency_blocker_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_chromadb(_name: str):
        raise ImportError("synthetic missing dependency")

    monkeypatch.setattr("sos.memory.chroma.importlib.import_module", missing_chromadb)
    store = ChromaMemoryStore(enabled=True)

    with pytest.raises(RuntimeError, match="CVE-2026-45829"):
        store.list("session")
    assert store._client is None
