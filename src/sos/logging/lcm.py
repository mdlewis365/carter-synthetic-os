# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Redacted Lifecycle Context Monitor (LCM) facade."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from .events import EventRecorder, LifecycleEvent
from .oprep import OperationReport, build_operation_report


class LifecycleMonitor:
    """Collect bounded metadata and produce content-free operational reports."""

    def __init__(self, recorder: EventRecorder | None = None) -> None:
        self.recorder = recorder or EventRecorder()

    def mark(
        self,
        event_type: str,
        *,
        request_id: str | None = None,
        session_id: str | None = None,
        status: str = "ok",
        metadata: Mapping[str, Any] | None = None,
    ) -> LifecycleEvent:
        return self.recorder.record(
            event_type,
            request_id=request_id,
            session_id=session_id,
            status=status,
            metadata=metadata,
        )

    def operation_report(
        self,
        *,
        artifact_hashes: Mapping[str, str] | None = None,
        generated_at: datetime | None = None,
    ) -> OperationReport:
        return build_operation_report(
            self.recorder.snapshot(),
            artifact_hashes=artifact_hashes,
            generated_at=generated_at,
        )

    def clear(self) -> None:
        self.recorder.clear()
