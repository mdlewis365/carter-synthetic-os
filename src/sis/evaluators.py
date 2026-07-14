# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Deterministic SIS candidate evaluators and output governance."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from .evaluator_aggregation import GateResult, aggregate_gate_results
from .invariant_claim_validator import InvariantFields, validate_invariant_claim
from .invention_mode_enum import InventionMode, requires_physical_feasibility
from .novelty_risk_scoring import score_candidate
from .rejection_boundary_validation import evaluate_rejection_boundaries

REQUIRED_CAVEATS = [
    "Independent technical validation is required.",
    "Prior-art review is required.",
    "Patentability and freedom-to-operate analysis are required.",
    "Safety and regulatory assessment are required.",
    "Experimental confirmation is required.",
]


def evaluate_candidate(
    candidate: Mapping[str, Any],
    mode: InventionMode,
    mcm_result: Mapping[str, Any],
) -> dict[str, Any]:
    text = " ".join(
        str(candidate.get(name) or "")
        for name in ("core_mechanism", "operating_principle", "novelty_delta")
    )
    boundaries = evaluate_rejection_boundaries(text)
    invariant = candidate.get("invariant")
    invariant_map = invariant if isinstance(invariant, Mapping) else {}
    invariant_result = validate_invariant_claim(
        text,
        InvariantFields(
            invariant_claim=_text_or_none(invariant_map.get("invariant_claim")),
            invariant_definition=_text_or_none(invariant_map.get("invariant_definition")),
            before_state=_text_or_none(invariant_map.get("before_state")),
            after_state=_text_or_none(invariant_map.get("after_state")),
            transition_operator=_text_or_none(invariant_map.get("transition_operator")),
            constraint_description=_text_or_none(invariant_map.get("constraint_description")),
            removal_test=_text_or_none(invariant_map.get("removal_test")),
        ),
    )
    falsifiable = bool(str(candidate.get("falsifiable_test") or "").strip())
    risks = candidate.get("feasibility_risks")
    risk_count = len(risks) if isinstance(risks, list) else 0
    novelty_risk = score_candidate(
        novelty_delta_present=bool(str(candidate.get("novelty_delta") or "").strip()),
        rejected_by_boundary_count=len(boundaries.hits),
        feasibility_risk_count=risk_count,
        falsifiable_test_present=falsifiable,
    )
    feasibility_gate = _feasibility_gate(mode, mcm_result)
    gates = [
        GateResult(
            "rejection_boundaries",
            boundaries.passed,
            max(0.0, 1.0 - 0.35 * len(boundaries.hits)),
            [hit.reason for hit in boundaries.hits]
            or ["No deterministic collapse pattern matched."],
            (
                ["Revise or reject candidates that match a collapse pattern."]
                if boundaries.hits
                else []
            ),
        ),
        GateResult(
            "invariant_audit",
            invariant_result.passed,
            invariant_result.score,
            invariant_result.reasons,
            [f"Provide invariant field: {name}." for name in invariant_result.missing_fields],
        ),
        GateResult(
            "falsifiability",
            falsifiable,
            1.0 if falsifiable else 0.25,
            (
                ["A falsifiable test is present."]
                if falsifiable
                else ["No falsifiable test was supplied."]
            ),
            [] if falsifiable else ["Define a controlled rejection test."],
        ),
        feasibility_gate,
        GateResult(
            "prior_art_review",
            False,
            0.6,
            ["No repository workflow can establish novelty or patentability."],
            ["Perform an independent prior-art and patent review."],
        ),
    ]
    aggregate = aggregate_gate_results(gates)
    return {
        "rejection_boundaries": asdict(boundaries),
        "invariant_audit": asdict(invariant_result),
        "novelty_risk_score": asdict(novelty_risk),
        "gate_results": [asdict(gate) for gate in gates],
        "aggregate": asdict(aggregate),
    }


def govern_output(candidate_valid: bool, evaluation: Mapping[str, Any]) -> dict[str, Any]:
    aggregate = evaluation.get("aggregate") if isinstance(evaluation, Mapping) else {}
    hard_rejected = not candidate_valid
    if isinstance(aggregate, Mapping):
        hard_rejected = hard_rejected or (
            not bool(aggregate.get("passed")) and float(aggregate.get("score") or 0.0) < 0.6
        )
    status = "rejected" if hard_rejected else "hypothesis_requires_independent_review"
    return {
        "status": status,
        "candidate_is_hypothesis": True,
        "human_review_required": True,
        "prior_art_status": "not_assessed",
        "patent_status": "not_assessed",
        "safety_status": "not_assessed",
        "experimental_status": "not_validated",
        "caveats": list(REQUIRED_CAVEATS),
        "release_boundary": (
            "SIS generates research candidates only; it does not establish novelty, "
            "patentability, feasibility, safety, or experimental validity."
        ),
    }


def _feasibility_gate(
    mode: InventionMode,
    mcm_result: Mapping[str, Any],
) -> GateResult:
    status = str(mcm_result.get("status") or "not_requested")
    if status == "computed":
        health = mcm_result.get("mcm_run_health")
        health_map = health if isinstance(health, Mapping) else {}
        failed = _nonnegative_int(health_map.get("constraint_failed"))
        unknown = _nonnegative_int(health_map.get("constraint_unknown"))
        blocking = health_map.get("blocking_failures")
        blocking_failures = list(blocking) if isinstance(blocking, (list, tuple)) else []
        computed_ok = health_map.get("mcm_computed_ok") is True

        if computed_ok and failed == 0 and unknown == 0 and not blocking_failures:
            return GateResult(
                "mcm_feasibility",
                True,
                0.9,
                ["The requested deterministic feasibility calculation completed cleanly."],
            )

        reasons = [
            "The deterministic feasibility calculation completed, but clean run health "
            "was not confirmed."
        ]
        if failed:
            reasons.append(f"MCM reported {failed} failed constraint check(s).")
        if unknown:
            reasons.append(f"MCM reported {unknown} unknown constraint check(s).")
        if failed is None or unknown is None:
            reasons.append("MCM constraint health counts were unavailable or invalid.")
        if blocking_failures:
            reasons.append("MCM reported blocking failures.")
        return GateResult(
            "mcm_feasibility",
            False,
            0.3,
            reasons,
            ["Resolve MCM run-health and constraint diagnostics before feasibility review."],
        )
    if status not in {"not_requested", "not_required"}:
        return GateResult(
            "mcm_feasibility",
            False,
            0.3,
            [f"Deterministic feasibility status is {status}."],
            ["Resolve MCM diagnostics before feasibility review."],
        )
    if requires_physical_feasibility(mode):
        return GateResult(
            "mcm_feasibility",
            False,
            0.6,
            ["Physical feasibility computation was not requested."],
            ["Define and run an appropriate deterministic feasibility case."],
        )
    return GateResult(
        "mcm_feasibility",
        True,
        0.8,
        ["This mode does not require a physical MCM calculation at candidate generation."],
    )


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if result >= 0 else None


def _text_or_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
