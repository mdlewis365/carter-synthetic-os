# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
# Public-safe excerpt adapted from the private implementation.
"""Bounded invention modes used by the ideation system."""

from __future__ import annotations

from enum import StrEnum


class InventionMode(StrEnum):
    MECHANISM_DISCOVERY = "mechanism-discovery"
    SYSTEM_ARCHITECTURE = "system-architecture"
    PROCESS_INNOVATION = "process-innovation"
    ALGORITHMIC_METHOD = "algorithmic-method"
    HYBRID_SYSTEM_DEVELOPMENT = "hybrid-system-development"
    CONSTRAINT_INVERSION = "constraint-inversion"


def normalize_mode(value: object) -> InventionMode:
    """Engineering capability: prevent prompt drift from mode spelling variants."""

    text = str(value or "").strip().lower().replace("_", "-")
    aliases = {
        "mechanism": InventionMode.MECHANISM_DISCOVERY,
        "architecture": InventionMode.SYSTEM_ARCHITECTURE,
        "process": InventionMode.PROCESS_INNOVATION,
        "algorithm": InventionMode.ALGORITHMIC_METHOD,
        "hybrid": InventionMode.HYBRID_SYSTEM_DEVELOPMENT,
        "constraint": InventionMode.CONSTRAINT_INVERSION,
    }
    for mode in InventionMode:
        if text == mode.value:
            return mode
    if text in aliases:
        return aliases[text]
    raise ValueError(f"Unknown invention mode: {value!r}")


def requires_physical_feasibility(mode: InventionMode) -> bool:
    return mode in {
        InventionMode.MECHANISM_DISCOVERY,
        InventionMode.HYBRID_SYSTEM_DEVELOPMENT,
        InventionMode.CONSTRAINT_INVERSION,
    }


if __name__ == "__main__":
    assert normalize_mode("system_architecture") == InventionMode.SYSTEM_ARCHITECTURE
    assert requires_physical_feasibility(InventionMode.CONSTRAINT_INVERSION)
