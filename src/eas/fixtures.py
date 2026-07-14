# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Deterministic, unmistakably synthetic public demonstration fixtures."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_FIXTURES: dict[str, dict[str, Any]] = {
    "synthetic_thermal_enclosure_v1": {
        "computation_id": "synthetic-thermal-enclosure-v1",
        "mode": "review-design",
        "objective": "Sum two synthetic heat loads for a public demonstration.",
        "operation": "sum",
        "variables": {
            "electronics_heat": {"value": 120.0, "unit": "W", "source": "synthetic_fixture"},
            "ambient_heat_gain": {"value": 30.0, "unit": "W", "source": "synthetic_fixture"},
        },
        "requested_output": "total_synthetic_heat_load",
        "constraints": [
            {
                "name": "synthetic_electronics_heat_limit",
                "lhs": "electronics_heat",
                "comparator": "<=",
                "rhs": 150.0,
                "unit": "W",
                "description": "Synthetic demonstration limit; not a design requirement.",
            }
        ],
        "sensitivity": {
            "enabled": True,
            "variables": {"electronics_heat": {"percent": 10.0}},
            "outputs": ["total_synthetic_heat_load"],
        },
        "fixture_notice": (
            "All values are synthetic demonstration data and are not suitable for design use."
        ),
    }
}


def fixture_mcm_request(fixture_id: object) -> dict[str, Any] | None:
    fixture = _FIXTURES.get(str(fixture_id or "").strip())
    return deepcopy(fixture) if fixture else None
