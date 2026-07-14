# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Privacy-preserving lifecycle metadata and operational reports."""

from .events import EventRecorder, LifecycleEvent, sanitize_metadata
from .lcm import LifecycleMonitor
from .oprep import OperationReport, build_operation_report

__all__ = [
    "EventRecorder",
    "LifecycleEvent",
    "LifecycleMonitor",
    "OperationReport",
    "build_operation_report",
    "sanitize_metadata",
]
