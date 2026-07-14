# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
# Public-safe excerpt adapted from the private implementation.
"""Public-safe workflow state object for ideation runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum


class WorkflowStage(StrEnum):
    INPUT_VALIDATED = "input_validated"
    CANDIDATE_GENERATED = "candidate_generated"
    GATES_EVALUATED = "gates_evaluated"
    NEEDS_REVISION = "needs_revision"
    PUBLIC_SUMMARY_READY = "public_summary_ready"
    REJECTED = "rejected"


@dataclass
class WorkflowState:
    """Engineering capability: track state without raw prompts or private concepts."""

    run_id: str
    stage: WorkflowStage = WorkflowStage.INPUT_VALIDATED
    invention_mode: str = "unknown"
    candidate_title: str | None = None
    public_candidate_summary: str | None = None
    gate_results: dict[str, str] = field(default_factory=dict)
    revision_count: int = 0

    def advance(self, stage: WorkflowStage) -> None:
        self.stage = stage

    def public_dict(self) -> dict:
        data = asdict(self)
        data["stage"] = self.stage.value
        return data


if __name__ == "__main__":
    state = WorkflowState("run-001", invention_mode="constraint-inversion")
    state.candidate_title = "Public demo candidate"
    state.gate_results["invariant_audit"] = "passed"
    state.advance(WorkflowStage.GATES_EVALUATED)
    assert state.public_dict()["stage"] == "gates_evaluated"
