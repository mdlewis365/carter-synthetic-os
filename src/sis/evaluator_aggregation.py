# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
# Public-safe excerpt adapted from the private implementation.
"""Evaluator aggregation for novelty and feasibility gates."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    score: float
    reasons: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AggregateEvaluation:
    passed: bool
    score: float
    blocking_gate: str | None
    reasons: list[str]
    required_actions: list[str]


def aggregate_gate_results(results: list[GateResult]) -> AggregateEvaluation:
    """Engineering capability: weak candidates are killed, not polished."""

    if not results:
        return AggregateEvaluation(False, 0.0, "missing_gates", ["No gate results."], [])

    reasons: list[str] = []
    actions: list[str] = []
    for result in results:
        reasons.extend(f"{result.name}: {reason}" for reason in result.reasons)
        actions.extend(result.required_actions)

        # Mirrors the private short-circuit pattern: early hard failures stop later polish.
        if not result.passed and result.score < 0.6:
            return AggregateEvaluation(False, result.score, result.name, reasons, actions)

    passed = all(result.passed for result in results)
    score = min(result.score for result in results)
    blocking = None if passed else next(result.name for result in results if not result.passed)
    return AggregateEvaluation(passed, score, blocking, reasons, actions)


if __name__ == "__main__":
    evaluation = aggregate_gate_results(
        [
            GateResult("negative_prior_art", True, 0.9, ["No motif hit."]),
            GateResult("invariant_audit", False, 0.3, ["Missing removal test."], ["Add removal test."]),
        ]
    )
    assert evaluation.blocking_gate == "invariant_audit"
