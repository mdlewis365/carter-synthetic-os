# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json

import pytest

from sis.invention_mode_enum import InventionMode
from sis.workflow import IdeationWorkflow

pytestmark = pytest.mark.integration


def inspection_fixture_payload() -> dict:
    return {
        "fixture_id": "synthetic_inspection_scheduler_v1",
        "problem_statement": (
            "Explore a bounded scheduling architecture for a synthetic inspection fixture."
        ),
        "mode": "system-architecture",
    }


def test_sis_fixture_runs_offline_as_explicit_hypothesis() -> None:
    result = IdeationWorkflow().run(inspection_fixture_payload())
    assert result["status"] == "hypothesis_requires_independent_review"
    assert result["backend"]["kind"] == "mock"
    assert result["backend"]["is_language_model"] is False
    assert result["scientist_input"]["domain"] == "synthetic inspection scheduling"
    assert result["candidate"]["hypothesis"] is True
    assert result["candidate"]["source"] == "deterministic-synthetic-template"
    assert result["candidate_validation"]["valid"] is True
    assert result["governance"]["prior_art_status"] == "not_assessed"
    assert result["governance"]["patent_status"] == "not_assessed"
    assert result["governance"]["experimental_status"] == "not_validated"
    assert len(result["governance"]["caveats"]) == 5
    assert result["human_review_required"] is True
    assert result["execution_metadata"]["candidate_generation_is_deterministic"] is True
    json.dumps(result)


def test_sis_mock_fixture_output_is_deterministic() -> None:
    workflow = IdeationWorkflow()
    assert workflow.run(inspection_fixture_payload()) == workflow.run(inspection_fixture_payload())


@pytest.mark.parametrize("mode", [item.value for item in InventionMode])
def test_all_sis_modes_produce_structured_candidates(mode: str) -> None:
    result = IdeationWorkflow().run(
        {
            "mode": mode,
            "domain": "synthetic laboratory fixture",
            "framing": "Form a falsifiable candidate for offline test coverage.",
        }
    )
    assert result["candidate_validation"]["valid"] is True
    assert result["candidate"]["invention_mode"] == mode
    assert result["governance"]["candidate_is_hypothesis"] is True


def test_sis_optional_mcm_feasibility_uses_deterministic_engine() -> None:
    payload = {
        "mode": "mechanism-discovery",
        "domain": "synthetic force fixture",
        "framing": "Test a bounded force-combination hypothesis.",
        "mcm_request": {
            "operation": "sum",
            "inputs": {"force_a": 2.0, "force_b": 3.0},
            "requested_output": "synthetic_force",
        },
    }
    result = IdeationWorkflow().run(payload)
    assert result["mcm_feasibility"]["status"] == "computed"
    assert result["mcm_feasibility"]["outputs"]["synthetic_force"] == 5.0
    gate = next(
        item for item in result["evaluation"]["gate_results"] if item["name"] == "mcm_feasibility"
    )
    assert gate["passed"] is True


def test_sis_mcm_feasibility_rejects_computed_result_with_failed_constraint() -> None:
    result = IdeationWorkflow().run(
        {
            "mode": "mechanism-discovery",
            "domain": "synthetic force fixture",
            "framing": "Test a bounded force-combination hypothesis.",
            "mcm_request": {
                "operation": "sum",
                "variables": {
                    "force_a": {"value": 2.0, "unit": "N"},
                    "force_b": {"value": 3.0, "unit": "N"},
                },
                "requested_output": "synthetic_force",
                "constraints": [
                    {
                        "name": "synthetic_force_a_limit",
                        "lhs": "force_a",
                        "comparator": "<=",
                        "rhs": 1.0,
                        "unit": "N",
                    }
                ],
            },
        }
    )

    assert result["mcm_feasibility"]["status"] == "computed"
    assert result["mcm_feasibility"]["mcm_run_health"]["mcm_computed_ok"] is False
    gate = next(
        item for item in result["evaluation"]["gate_results"] if item["name"] == "mcm_feasibility"
    )
    assert gate["passed"] is False
    assert gate["score"] == 0.3
    assert any("failed constraint" in reason for reason in gate["reasons"])


def test_sis_provider_metadata_is_not_reflected() -> None:
    class StructuredProvider:
        provider_name = "synthetic-structured-provider"

        def generate_ideation_candidate(self, context: dict) -> dict:
            return {
                "title": "Synthetic provider candidate",
                "field": "synthetic scheduling",
                "core_mechanism": "Apply a causal constraint before each transition.",
                "operating_principle": "Reject transitions that fail the constraint.",
                "novelty_delta": "Make the removal test explicit.",
                "falsifiable_test": "Remove the constraint and compare outcomes.",
                "feasibility_risks": ["The synthetic effect may not reproduce."],
                "raw_response": {"api_key": "must-not-survive"},
            }

    result = IdeationWorkflow().run(
        inspection_fixture_payload(),
        provider=StructuredProvider(),
    )
    assert result["candidate_validation"]["valid"] is True
    assert "raw_response" not in result["candidate"]
    assert "must-not-survive" not in json.dumps(result)


def test_sis_provider_exception_message_is_not_reflected() -> None:
    class FailingProvider:
        def generate_ideation_candidate(self, context: dict) -> dict:
            raise RuntimeError("synthetic-secret-must-not-survive")

    result = IdeationWorkflow().run(
        inspection_fixture_payload(),
        provider=FailingProvider(),
    )
    assert result["status"] == "provider_failure"
    assert "Candidate provider failed." in result["errors"]
    assert "synthetic-secret-must-not-survive" not in json.dumps(result)
