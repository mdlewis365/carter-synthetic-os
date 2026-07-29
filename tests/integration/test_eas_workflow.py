# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json

import pytest

from eas.workflow import EngineeringWorkflow

pytestmark = pytest.mark.integration


def thermal_fixture_payload() -> dict:
    return {
        "fixture_id": "synthetic_thermal_enclosure_v1",
        "problem_statement": "Evaluate the synthetic enclosure cooling fixture.",
        "mode": "review-design",
    }


def test_eas_fixture_runs_full_two_stage_workflow_offline() -> None:
    result = EngineeringWorkflow().run(thermal_fixture_payload())
    assert result["status"] == "advisory_ready"
    assert result["backend"] == {
        "kind": "mock",
        "name": "deterministic-synthetic-planner",
        "is_language_model": False,
    }
    assert result["schema_validation"]["valid"] is True
    assert result["mcm"]["result"]["status"] == "computed"
    assert result["mcm"]["result"]["outputs"]["total_synthetic_heat_load"] == 150.0
    assert result["mcm"]["constraint_summary"]["overall_pass"] is True
    assert result["mcm"]["sensitivity"]["enabled"] is True
    assert result["governance"]["governance_status"] == "needs_human_review"
    assert result["governance"]["public_release_gate"] == "mandatory_human_review"
    assert result["governance"]["professional_approval_status"] == "not_approved"
    assert result["governance"]["deterministic_gate_status"] == "computed_criteria_passed"
    assert result["engineering_decision_record"]["human_review_required"] is True
    assert result["decision_record_validation"]["valid"] is True
    assert result["final_response"]["human_review_required"] is True
    assert result["structured_plan"] == result["stage_one_plan"]
    assert result["computation"] == result["mcm"]
    assert result["execution_metadata"]["record_timestamp_source"] == ("fixed_synthetic_fixture")
    json.dumps(result)


def test_eas_mock_fixture_output_is_deterministic() -> None:
    workflow = EngineeringWorkflow()
    assert workflow.run(thermal_fixture_payload()) == workflow.run(thermal_fixture_payload())


def test_eas_provider_failure_is_structured_and_never_runs_invalid_plan() -> None:
    class FailingProvider:
        provider_name = "offline-failing-provider"

        def plan_engineering(self, context: dict) -> dict:
            raise RuntimeError("synthetic provider failure")

    result = EngineeringWorkflow().run(
        {
            "mode": "solve-problem",
            "problem_statement": "Synthetic provider failure test.",
        },
        provider=FailingProvider(),
    )
    assert result["status"] == "needs_input"
    assert result["schema_validation"]["valid"] is True
    assert result["mcm"]["result"]["status"] == "not_required"
    assert result["errors"] == ["Planning provider failed."]
    assert "synthetic provider failure" not in json.dumps(result)
    assert result["human_review_required"] is True


def test_eas_constructs_mcm_request_from_structured_top_level_fields() -> None:
    result = EngineeringWorkflow().run(
        {
            "mode": "solve-problem",
            "problem_statement": "Combine two labeled synthetic forces.",
            "operation": "sum",
            "variables": {
                "force_a": {"value": 2.0, "unit": "N"},
                "force_b": {"value": 3.0, "unit": "N"},
            },
            "requested_output": "combined_force",
            "constraints": [
                {
                    "name": "synthetic_force_limit",
                    "lhs": "force_a",
                    "comparator": "<=",
                    "rhs": 4.0,
                    "unit": "N",
                }
            ],
            "sensitivity": {
                "enabled": True,
                "variables": {"force_a": {"percent": 10.0}},
                "outputs": ["combined_force"],
            },
        }
    )
    constructed = result["stage_one_plan"]["mcm_request"]
    assert constructed["operation"] == "sum"
    assert result["mcm"]["result"]["outputs"]["combined_force"] == 5.0
    assert result["mcm"]["constraint_summary"]["overall_pass"] is True
    assert result["mcm"]["sensitivity"]["enabled"] is True


def test_eas_rejects_unbounded_mcm_expression_before_advisory() -> None:
    result = EngineeringWorkflow().run(
        {
            "mode": "solve-problem",
            "problem_statement": "Evaluate a deliberately unbounded synthetic expression.",
            "expression": '"A" * 1000000000',
            "requested_output": "unsafe_result",
        }
    )

    assert result["status"] == "needs_human_review"
    assert result["mcm"]["result"]["status"] == "unsupported"
    assert result["mcm"]["result"]["outputs"] == {}
    assert result["governance"]["governance_status"] == "needs_human_review"


def test_eas_computed_constraint_failure_requires_review_and_is_visible() -> None:
    result = EngineeringWorkflow().run(
        {
            "mode": "review-design",
            "problem_statement": "Evaluate a deliberately failing synthetic force limit.",
            "operation": "sum",
            "variables": {
                "force_a": {"value": 2.0, "unit": "N"},
                "force_b": {"value": 3.0, "unit": "N"},
            },
            "requested_output": "combined_force",
            "constraints": [
                {
                    "name": "synthetic_force_a_limit",
                    "lhs": "force_a",
                    "comparator": "<=",
                    "rhs": 1.0,
                    "unit": "N",
                }
            ],
        }
    )

    assert result["mcm"]["result"]["status"] == "computed"
    assert result["mcm"]["run_health"]["mcm_computed_ok"] is False
    assert result["mcm"]["constraint_summary"]["failed"] == 1
    assert result["status"] == "needs_human_review"
    assert result["governance"]["deterministic_gate_status"] == "computed_with_failure"
    assert "1 constraint check(s) failed" in result["advisory"]["summary"]


def test_eas_provider_can_propose_plan_but_cannot_approve_result() -> None:
    class StructuredProvider:
        provider_name = "synthetic-structured-provider"

        def __init__(self) -> None:
            self.context: dict = {}

        def plan_engineering(self, context: dict) -> dict:
            self.context = context
            return {
                "mode": "solve-problem",
                "problem_statement": context["request"]["problem_statement"],
                "objective": "Compute a labeled synthetic sum.",
                "assumptions": ["Inputs are synthetic."],
                "required_inputs": ["value_a", "value_b"],
                "equations": [],
                "constraints": [],
                "mcm_request": {
                    "operation": "sum",
                    "inputs": {"value_a": 4.0, "value_b": 6.0},
                    "requested_output": "synthetic_total",
                    "OPENAI_API_KEY": "must-not-survive",
                },
                "raw_provider_response": {"credential": "must-not-survive"},
            }

    provider = StructuredProvider()
    result = EngineeringWorkflow().run(
        {
            "mode": "solve-problem",
            "problem_statement": "Compute a synthetic provider-planned fixture.",
        },
        provider=provider,
    )
    assert result["status"] == "advisory_ready"
    assert result["backend"]["kind"] == "provider"
    assert result["mcm"]["result"]["outputs"]["synthetic_total"] == 10.0
    assert result["governance"]["governance_status"] == "needs_human_review"
    assert result["governance"]["public_release_gate"] == "mandatory_human_review"
    assert provider.context["selected_packs"]
    assert provider.context["selected_packs"][0]["guidance_text"].startswith("<!--")
    assert sum(len(pack["guidance_text"]) for pack in provider.context["selected_packs"]) <= 24_000
    serialized = json.dumps(result)
    assert "OPENAI_API_KEY" not in serialized
    assert "raw_provider_response" not in serialized
    assert "must-not-survive" not in serialized
