# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
# Public-safe excerpt adapted from the private implementation.
"""Novelty and risk scoring structure for ideation candidates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreComponent:
    name: str
    score: float
    rationale: str


@dataclass(frozen=True)
class NoveltyRiskScore:
    overall_score: float
    novelty: ScoreComponent
    collapse_resistance: ScoreComponent
    feasibility: ScoreComponent
    falsifiability: ScoreComponent
    review_required: bool


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def score_candidate(
    *,
    novelty_delta_present: bool,
    rejected_by_boundary_count: int,
    feasibility_risk_count: int,
    falsifiable_test_present: bool,
) -> NoveltyRiskScore:
    """Engineering capability: score structure, not persuasive prose."""

    novelty = ScoreComponent(
        "novelty",
        0.9 if novelty_delta_present else 0.2,
        "Novelty delta stated." if novelty_delta_present else "Novelty delta missing.",
    )
    collapse = ScoreComponent(
        "collapse_resistance",
        clamp(1.0 - 0.3 * rejected_by_boundary_count),
        f"{rejected_by_boundary_count} rejection boundary hit(s).",
    )
    feasibility = ScoreComponent(
        "feasibility",
        clamp(1.0 - 0.2 * feasibility_risk_count),
        f"{feasibility_risk_count} feasibility risk(s) listed.",
    )
    falsifiability = ScoreComponent(
        "falsifiability",
        1.0 if falsifiable_test_present else 0.25,
        "Falsifiable test present." if falsifiable_test_present else "Falsifiable test missing.",
    )
    overall = min(novelty.score, collapse.score, feasibility.score, falsifiability.score)
    return NoveltyRiskScore(overall, novelty, collapse, feasibility, falsifiability, overall < 0.65)


if __name__ == "__main__":
    score = score_candidate(
        novelty_delta_present=True,
        rejected_by_boundary_count=1,
        feasibility_risk_count=2,
        falsifiable_test_present=True,
    )
    assert 0.0 <= score.overall_score <= 1.0
