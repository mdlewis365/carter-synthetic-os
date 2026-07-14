# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Deterministic synthetic candidate fixtures for each public SIS mode."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .invention_mode_enum import InventionMode
from .scientist_input_schema import ScientistInput

_MODE_TITLES = {
    InventionMode.MECHANISM_DISCOVERY: "Reversible Boundary Mechanism Candidate",
    InventionMode.SYSTEM_ARCHITECTURE: "Separated Evidence and Action Architecture Candidate",
    InventionMode.PROCESS_INNOVATION: "Measured Transition Gate Process Candidate",
    InventionMode.ALGORITHMIC_METHOD: "Admissible-State Pruning Algorithm Candidate",
    InventionMode.HYBRID_SYSTEM_DEVELOPMENT: "Physical Boundary and Adjudicator Hybrid Candidate",
    InventionMode.CONSTRAINT_INVERSION: "Constraint-as-Enabler Candidate",
}


def deterministic_candidate(scientist_input: ScientistInput, mode: InventionMode) -> dict[str, Any]:
    """Return a transparent template candidate, not simulated model output."""

    domain = scientist_input.domain
    framing = scientist_input.framing
    mechanism_by_mode = {
        InventionMode.MECHANISM_DISCOVERY: (
            f"Apply a reversible boundary constraint to {domain}, then compare behavior "
            "with and without that constraint."
        ),
        InventionMode.SYSTEM_ARCHITECTURE: (
            f"Separate evidence collection, deterministic adjudication, and human-approved "
            f"action for {domain}; the approval constraint is causally necessary."
        ),
        InventionMode.PROCESS_INNOVATION: (
            f"Gate each {domain} process transition on a measured acceptance constraint "
            "and retain rejected states for review."
        ),
        InventionMode.ALGORITHMIC_METHOD: (
            f"Represent admissible {domain} states explicitly and prune transitions that "
            "violate a declared constraint before ranking survivors."
        ),
        InventionMode.HYBRID_SYSTEM_DEVELOPMENT: (
            f"Couple a reversible physical boundary in {domain} to a deterministic "
            "adjudicator, with human approval as a necessary actuation constraint."
        ),
        InventionMode.CONSTRAINT_INVERSION: (
            f"Treat the stated {domain} constraint as an enabling boundary and test "
            "whether removing it eliminates the proposed effect."
        ),
    }
    principle_by_mode = {
        InventionMode.MECHANISM_DISCOVERY: (
            "Difference the constrained and unconstrained observations."
        ),
        InventionMode.SYSTEM_ARCHITECTURE: (
            "Prevent evidence-generation components from authorizing action."
        ),
        InventionMode.PROCESS_INNOVATION: (
            "Advance only when the measured transition predicate passes."
        ),
        InventionMode.ALGORITHMIC_METHOD: (
            "Filter inadmissible transitions before applying a deterministic rank."
        ),
        InventionMode.HYBRID_SYSTEM_DEVELOPMENT: (
            "Correlate physical-state evidence with bounded digital adjudication."
        ),
        InventionMode.CONSTRAINT_INVERSION: (
            "Use removal of the constraint as the causal falsification test."
        ),
    }
    invariant = {
        "invariant_claim": (
            "Admissible-state membership changes only through the declared transition."
        ),
        "invariant_definition": "Membership in the explicitly declared admissible-state set.",
        "before_state": "Candidate state has not passed the declared constraint.",
        "after_state": "Candidate state has passed the declared constraint.",
        "transition_operator": "Apply the declared constraint check.",
        "constraint_description": "The acceptance constraint is necessary for the proposed effect.",
        "removal_test": "Remove the constraint and test whether the claimed effect disappears.",
    }
    return {
        "schema": "sis.concept_candidate.v1",
        "title": _MODE_TITLES[mode],
        "field": domain,
        "invention_mode": mode.value,
        "hypothesis": True,
        "source": "deterministic-synthetic-template",
        "framing": framing,
        "core_mechanism": mechanism_by_mode[mode],
        "operating_principle": principle_by_mode[mode],
        "novelty_delta": (
            "Candidate delta to investigate: make the causal constraint and its removal "
            "test explicit before optimization."
        ),
        "invariant": invariant,
        "feasibility_risks": [
            "The proposed causal effect may not survive controlled testing.",
            "Measurement resolution may be insufficient to distinguish the states.",
        ],
        "falsifiable_test": (
            "Run matched trials with the declared constraint present and removed; reject "
            "the candidate if the predicted effect is not distinguishable."
        ),
        "rejection_checks": list(scientist_input.rejection_boundaries),
    }


def normalize_provider_candidate(
    raw_candidate: Any,
    scientist_input: ScientistInput,
    mode: InventionMode,
) -> dict[str, Any]:
    source = dict(raw_candidate) if isinstance(raw_candidate, Mapping) else {}
    candidate: dict[str, Any] = {}
    candidate["schema"] = "sis.concept_candidate.v1"
    candidate["title"] = str(source.get("title") or "")[:300]
    candidate["field"] = str(source.get("field") or scientist_input.domain)[:300]
    candidate["invention_mode"] = mode.value
    candidate["hypothesis"] = True
    candidate["source"] = "configured-provider"
    candidate["framing"] = scientist_input.framing
    for name in (
        "core_mechanism",
        "operating_principle",
        "novelty_delta",
        "falsifiable_test",
    ):
        candidate[name] = str(source.get(name) or "")[:4000]
    candidate["feasibility_risks"] = _string_list(source.get("feasibility_risks"))
    candidate["rejection_checks"] = list(scientist_input.rejection_boundaries)
    invariant = source.get("invariant")
    invariant_fields = (
        "invariant_claim",
        "invariant_definition",
        "before_state",
        "after_state",
        "transition_operator",
        "constraint_description",
        "removal_test",
    )
    candidate["invariant"] = (
        {name: invariant.get(name) for name in invariant_fields}
        if isinstance(invariant, Mapping)
        else {}
    )
    return candidate


def validate_candidate(candidate: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(candidate, Mapping):
        return {"valid": False, "errors": ["candidate must be a JSON object"], "warnings": []}
    required = ("title", "field", "core_mechanism", "operating_principle", "falsifiable_test")
    for field_name in required:
        if not str(candidate.get(field_name) or "").strip():
            errors.append(f"{field_name} is required")
    if candidate.get("hypothesis") is not True:
        errors.append("candidate must be labeled as a hypothesis")
    if not isinstance(candidate.get("feasibility_risks"), list):
        errors.append("feasibility_risks must be a list")
    return {"valid": not errors, "errors": errors, "warnings": []}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item)[:1000] for item in value[:50] if str(item or "").strip()]
