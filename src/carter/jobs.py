# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Bounded in-memory jobs with mandatory session ownership."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class JobRecord:
    job_id: str
    owner_session_id: str
    kind: str
    status: str
    created_at: str
    updated_at: str
    events: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] | None = None
    error_code: str | None = None

    def public_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result.pop("owner_session_id", None)
        return result


class JobStore:
    def __init__(self, *, ttl_seconds: int = 900, max_jobs: int = 200) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_jobs = max_jobs
        self._lock = threading.RLock()
        self._jobs: dict[str, tuple[float, JobRecord]] = {}

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).isoformat()

    def _prune(self) -> None:
        cutoff = time.time() - self.ttl_seconds
        for job_id, (epoch, _) in list(self._jobs.items()):
            if epoch < cutoff:
                self._jobs.pop(job_id, None)
        while len(self._jobs) >= self.max_jobs:
            oldest = min(self._jobs, key=lambda key: self._jobs[key][0])
            self._jobs.pop(oldest, None)

    def create(self, owner_session_id: str, kind: str) -> JobRecord:
        owner = str(owner_session_id or "").strip()
        if not owner:
            raise ValueError("owner_session_id is required")
        now = self._timestamp()
        with self._lock:
            self._prune()
            job = JobRecord(
                job_id=secrets.token_urlsafe(18),
                owner_session_id=owner,
                kind=str(kind or "unknown")[:40],
                status="queued",
                created_at=now,
                updated_at=now,
            )
            self._jobs[job.job_id] = (time.time(), job)
            return job

    def append_event(
        self,
        owner_session_id: str,
        job_id: str,
        *,
        stage: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> JobRecord:
        with self._lock:
            job = self.get(owner_session_id, job_id)
            job.events.append(
                {
                    "sequence": len(job.events) + 1,
                    "timestamp": self._timestamp(),
                    "stage": str(stage)[:80],
                    "status": str(status)[:40],
                    "metadata": dict(metadata or {}),
                }
            )
            job.status = status
            job.updated_at = self._timestamp()
            self._jobs[job.job_id] = (time.time(), job)
            return job

    def complete(
        self,
        owner_session_id: str,
        job_id: str,
        result: dict[str, Any],
    ) -> JobRecord:
        with self._lock:
            job = self.get(owner_session_id, job_id)
            job.status = "completed"
            job.result = dict(result)
            job.updated_at = self._timestamp()
            self._jobs[job.job_id] = (time.time(), job)
            return job

    def get(self, owner_session_id: str, job_id: str) -> JobRecord:
        with self._lock:
            self._prune()
            stored = self._jobs.get(str(job_id))
            if stored is None:
                raise KeyError("job_not_found")
            job = stored[1]
            if not secrets.compare_digest(job.owner_session_id, str(owner_session_id or "")):
                raise PermissionError("job_not_owned_by_session")
            return job

    def clear_owner(self, owner_session_id: str) -> int:
        with self._lock:
            owned = [
                job_id
                for job_id, (_, job) in self._jobs.items()
                if job.owner_session_id == owner_session_id
            ]
            for job_id in owned:
                self._jobs.pop(job_id, None)
            return len(owned)
