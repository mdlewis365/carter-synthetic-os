# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from sos.computation.mcm import process

pytestmark = pytest.mark.unit


def synthetic_sum_request() -> dict:
    return {
        "computation_id": "synthetic-unit-test",
        "operation": "sum",
        "variables": {
            "load_a": {"value": 12.0, "unit": "N", "source": "synthetic_fixture"},
            "load_b": {"value": 8.0, "unit": "N", "source": "synthetic_fixture"},
        },
        "requested_output": "combined_load",
        "constraints": [
            {
                "name": "synthetic_individual_limit",
                "lhs": "load_a",
                "comparator": "<=",
                "rhs": 15.0,
                "unit": "N",
            }
        ],
        "sensitivity": {
            "enabled": True,
            "variables": {"load_a": {"percent": 10.0}},
            "outputs": ["combined_load"],
        },
    }


def test_mcm_computes_constraints_units_and_sensitivity() -> None:
    result = process(synthetic_sum_request())
    assert result["status"] == "computed"
    assert result["outputs"]["combined_load"] == pytest.approx(20.0)
    check = result["constraint_checks"]["checks"][0]
    assert check["passes"] is True
    assert check["unit_validation"]["status"] == "valid"
    assert result["constraint_checks"]["summary"]["overall_pass"] is True
    assert result["sensitivity_analysis"]["enabled"] is True
    assert result["sensitivity_analysis"]["cases"][0]["varied_input"] == "load_a"
    assert result["mcm_run_health"]["mcm_computed_ok"] is True


def test_mcm_rejects_unsafe_expression_without_execution() -> None:
    result = process(
        {
            "expression": "__import__('os').system('echo unsafe')",
            "inputs": {},
            "requested_output": "unsafe",
        }
    )
    assert result["status"] == "unsupported"
    assert "could not be evaluated safely" in result["message"]
    assert result["outputs"] == {}


@pytest.mark.parametrize(
    "expression",
    [
        '"A" * 1000000000',
        "[1] * 1000000000",
        '"%1000000000s" % "A"',
        "['A' * 10000] * 10000",
        "2 ** 1000000000",
        "1e309",
    ],
)
def test_mcm_rejects_unbounded_or_non_finite_expression_results(
    expression: str,
) -> None:
    result = process(
        {
            "expression": expression,
            "inputs": {},
            "requested_output": "bounded_result",
        }
    )

    assert result["status"] == "unsupported"
    assert result["outputs"] == {}
    assert len(repr(result)) < 10000


def test_mcm_rejects_non_finite_operation_inputs() -> None:
    result = process(
        {
            "operation": "sum",
            "inputs": {"invalid": float("nan")},
            "requested_output": "bounded_result",
        }
    )

    assert result["status"] in {"needs_human_review", "unsupported", "error"}
    assert result["outputs"] == {}


def test_mcm_non_finite_string_cannot_pass_constraint_governance() -> None:
    request = synthetic_sum_request()
    request["variables"]["load_a"]["value"] = "NaN"

    result = process(request)

    checks = result.get("constraint_checks", {}).get("checks", [])
    assert not checks or checks[0].get("passes") is not True
    assert result["mcm_run_health"]["mcm_computed_ok"] is False


def test_mcm_missing_required_input_needs_review() -> None:
    result = process(
        {
            "operation": "sum",
            "variables": {
                "missing_value": {
                    "value": None,
                    "unit": "N",
                    "required_for_computation": True,
                }
            },
        }
    )
    assert result["status"] == "needs_human_review"
    assert result["mcm_run_health"]["mcm_computed_ok"] is False
