# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Canonical modes for the Engineering Assistance System."""

from __future__ import annotations

import re
from enum import StrEnum


class EngineeringMode(StrEnum):
    SOLVE_PROBLEM = "solve-problem"
    DIAGNOSE_ROOT_CAUSE = "diagnose-root-cause"
    REVIEW_DESIGN = "review-design"
    SUGGEST_IMPROVEMENTS = "suggest-improvements"
    EXPLORE_NOVEL_SOLUTION = "explore-novel-solution"


_ALIASES = {
    "solve": EngineeringMode.SOLVE_PROBLEM,
    "solve-the-problem": EngineeringMode.SOLVE_PROBLEM,
    "problem-solving": EngineeringMode.SOLVE_PROBLEM,
    "diagnose": EngineeringMode.DIAGNOSE_ROOT_CAUSE,
    "root-cause": EngineeringMode.DIAGNOSE_ROOT_CAUSE,
    "root-cause-analysis": EngineeringMode.DIAGNOSE_ROOT_CAUSE,
    "review": EngineeringMode.REVIEW_DESIGN,
    "design-review": EngineeringMode.REVIEW_DESIGN,
    "improve": EngineeringMode.SUGGEST_IMPROVEMENTS,
    "improvements": EngineeringMode.SUGGEST_IMPROVEMENTS,
    "suggest-improvement": EngineeringMode.SUGGEST_IMPROVEMENTS,
    "explore": EngineeringMode.EXPLORE_NOVEL_SOLUTION,
    "novel-solution": EngineeringMode.EXPLORE_NOVEL_SOLUTION,
    "ideate": EngineeringMode.EXPLORE_NOVEL_SOLUTION,
}


def normalize_mode(value: object) -> EngineeringMode:
    """Normalize UI/provider spelling without silently inventing a mode."""

    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    for mode in EngineeringMode:
        if text == mode.value:
            return mode
    if text in _ALIASES:
        return _ALIASES[text]
    raise ValueError(f"Unknown engineering mode: {value!r}")


def supported_modes() -> tuple[str, ...]:
    return tuple(mode.value for mode in EngineeringMode)
