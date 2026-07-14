# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
# Public-safe excerpt adapted from the private implementation.
"""Rejection-boundary validation for weak invention candidates."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BoundaryHit:
    boundary: str
    reason: str


@dataclass(frozen=True)
class BoundaryResult:
    passed: bool
    hits: list[BoundaryHit] = field(default_factory=list)


REJECTION_BOUNDARIES = {
    "parameter_tuning": (
        r"\b(parameter|coefficient|threshold)\b.*\b(tune|adjust|optimi[sz]e)\b",
        "Candidate appears reducible to tuning a known parameter.",
    ),
    "generic_control_wrapper": (
        r"\b(feedback|controller|closed loop|pid)\b",
        "Candidate may be a standard control wrapper rather than a new mechanism.",
    ),
    "missing_causal_constraint": (
        r"\bconstraint\b",
        "Candidate must explain why the constraint is causally necessary.",
    ),
}


def evaluate_rejection_boundaries(candidate_text: str) -> BoundaryResult:
    """Engineering capability: reject collapse patterns before refinement."""

    text = str(candidate_text or "").lower()
    hits: list[BoundaryHit] = []

    for name, (pattern, reason) in REJECTION_BOUNDARIES.items():
        matched = re.search(pattern, text, flags=re.IGNORECASE)
        if name == "missing_causal_constraint":
            if not matched:
                hits.append(BoundaryHit(name, reason))
        elif matched:
            hits.append(BoundaryHit(name, reason))

    return BoundaryResult(passed=not hits, hits=hits)


if __name__ == "__main__":
    result = evaluate_rejection_boundaries("Optimize a controller threshold.")
    assert result.passed is False
    assert any(hit.boundary == "parameter_tuning" for hit in result.hits)
