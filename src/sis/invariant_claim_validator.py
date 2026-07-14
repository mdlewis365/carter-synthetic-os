# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
# Public-safe excerpt adapted from the private implementation.
"""Invariant claim validator for mechanism-grade ideation outputs."""

from __future__ import annotations

from dataclasses import dataclass, field

STRUCTURAL_CLAIM_WORDS = (
    "topology",
    "topological",
    "invariant",
    "phase",
    "state space",
    "graph connectivity",
)


@dataclass(frozen=True)
class InvariantFields:
    invariant_claim: str | None = None
    invariant_definition: str | None = None
    before_state: str | None = None
    after_state: str | None = None
    transition_operator: str | None = None
    constraint_description: str | None = None
    removal_test: str | None = None


@dataclass(frozen=True)
class InvariantValidation:
    passed: bool
    score: float
    missing_fields: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def validate_invariant_claim(raw_text: str, fields: InvariantFields) -> InvariantValidation:
    """Engineering capability: structural novelty claims require formal anchors."""

    text = str(raw_text or "").lower()
    strict = any(word in text for word in STRUCTURAL_CLAIM_WORDS)
    if not strict:
        return InvariantValidation(True, 0.8, reasons=["No explicit invariant claim detected."])

    missing = [name for name, value in fields.__dict__.items() if not str(value or "").strip()]
    if missing:
        return InvariantValidation(
            False,
            0.0,
            missing,
            ["Structural novelty claim is missing required invariant fields."],
        )

    if fields.before_state.strip().lower() == fields.after_state.strip().lower():
        return InvariantValidation(
            False,
            0.2,
            ["before_state", "after_state"],
            ["Before and after states are identical."],
        )

    return InvariantValidation(True, 1.0, reasons=["Invariant declaration is complete."])


if __name__ == "__main__":
    validation = validate_invariant_claim(
        "The concept changes graph connectivity as an invariant.",
        InvariantFields(invariant_claim="connectivity changes"),
    )
    assert validation.passed is False
    assert "removal_test" in validation.missing_fields
