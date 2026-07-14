# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from eas.modes import EngineeringMode, normalize_mode, supported_modes
from eas.packs import discover_packs, select_packs
from eas.schemas import build_deterministic_plan, normalize_request, validate_stage_one_plan

pytestmark = pytest.mark.unit


def test_mode_normalization_covers_public_modes() -> None:
    assert normalize_mode("solve_problem") is EngineeringMode.SOLVE_PROBLEM
    assert normalize_mode("Root Cause Analysis") is EngineeringMode.DIAGNOSE_ROOT_CAUSE
    assert normalize_mode("design review") is EngineeringMode.REVIEW_DESIGN
    assert normalize_mode("improve") is EngineeringMode.SUGGEST_IMPROVEMENTS
    assert normalize_mode("novel solution") is EngineeringMode.EXPLORE_NOVEL_SOLUTION
    assert len(supported_modes()) == 5


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown engineering mode"):
        normalize_mode("unbounded-autonomous-design")


def test_pack_registry_contains_all_audit_cleared_markdown_files() -> None:
    registry = discover_packs()
    assert len(registry) == 18
    assert "modes/review_design_pack" in registry
    assert "domains/software_systems_engineering_pack" in registry
    assert all(len(pack.sha256) == 64 for pack in registry.values())


def test_pack_selection_combines_mode_and_domain_rules() -> None:
    selected = select_packs(
        "review-design",
        "Review a synthetic pump loop for hydraulic head loss.",
    )
    ids = [pack.pack_id for pack in selected]
    assert ids[0] == "modes/review_design_pack"
    assert "fluid_pump_loop_pack" in ids


def test_stage_one_fixture_plan_validates() -> None:
    request = normalize_request(
        {
            "fixture_id": "synthetic_thermal_enclosure_v1",
            "mode": "review-design",
            "problem_statement": "Evaluate the synthetic enclosure cooling fixture.",
        }
    )
    plan = build_deterministic_plan(request, ["modes/review_design_pack"])
    validation = validate_stage_one_plan(plan)
    assert validation.valid is True
    assert plan["mcm_required"] is True
    assert plan["planning_backend"]["is_language_model"] is False
    assert plan["synthetic_fixture"] == "synthetic_thermal_enclosure_v1"


def test_plan_requires_problem_statement_and_mcm_request() -> None:
    plan = {
        "schema": "eas.stage_one_plan.v1",
        "mode": "solve-problem",
        "problem_statement": "",
        "assumptions": [],
        "required_inputs": [],
        "equations": [],
        "constraints": [],
        "selected_packs": [],
        "mcm_required": True,
        "mcm_request": None,
        "planning_backend": {},
        "human_review_required": True,
    }
    validation = validate_stage_one_plan(plan)
    assert validation.valid is False
    assert "problem_statement is required" in validation.errors
    assert "mcm_request is required when mcm_required is true" in validation.errors


def test_normalized_mcm_request_drops_credential_shaped_keys() -> None:
    request = normalize_request(
        {
            "mode": "solve-problem",
            "problem_statement": "Synthetic secret-redaction fixture.",
            "mcm_request": {
                "OPENAI_API_KEY": "must-not-survive",
                "variables": {
                    "load": {"value": 1.0, "unit": "N"},
                    "provider_access_token": "must-not-survive",
                },
            },
        }
    )
    mcm_request = request["mcm_request"]
    assert "OPENAI_API_KEY" not in mcm_request
    assert "provider_access_token" not in mcm_request["variables"]
