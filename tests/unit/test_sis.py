# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from sis.invariant_claim_validator import InvariantFields, validate_invariant_claim
from sis.invention_mode_enum import InventionMode, normalize_mode
from sis.rejection_boundary_validation import evaluate_rejection_boundaries

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("mechanism", InventionMode.MECHANISM_DISCOVERY),
        ("system_architecture", InventionMode.SYSTEM_ARCHITECTURE),
        ("process", InventionMode.PROCESS_INNOVATION),
        ("algorithm", InventionMode.ALGORITHMIC_METHOD),
        ("hybrid", InventionMode.HYBRID_SYSTEM_DEVELOPMENT),
        ("constraint", InventionMode.CONSTRAINT_INVERSION),
    ],
)
def test_invention_mode_normalization(value: str, expected: InventionMode) -> None:
    assert normalize_mode(value) is expected


def test_parameter_tuning_candidate_hits_rejection_boundary() -> None:
    result = evaluate_rejection_boundaries(
        "Adjust a parameter and optimize a generic feedback controller."
    )
    assert result.passed is False
    boundaries = {hit.boundary for hit in result.hits}
    assert "parameter_tuning" in boundaries
    assert "generic_control_wrapper" in boundaries
    assert "missing_causal_constraint" in boundaries


def test_structural_claim_requires_complete_invariant_fields() -> None:
    result = validate_invariant_claim(
        "The hypothesis changes graph connectivity.",
        InvariantFields(invariant_claim="Connectivity changes."),
    )
    assert result.passed is False
    assert "removal_test" in result.missing_fields


def test_complete_invariant_claim_passes_structural_check() -> None:
    result = validate_invariant_claim(
        "The hypothesis changes graph connectivity.",
        InvariantFields(
            invariant_claim="Connectivity changes.",
            invariant_definition="Connected-region count.",
            before_state="Two regions.",
            after_state="One region.",
            transition_operator="Apply the boundary.",
            constraint_description="The boundary joins the regions.",
            removal_test="Remove the boundary and recover two regions.",
        ),
    )
    assert result.passed is True
