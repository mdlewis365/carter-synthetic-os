# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
# Public-safe excerpt adapted from the private implementation.
"""Public-safe concept output schema for generated invention candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class InvariantDeclaration:
    invariant_claim: str
    invariant_definition: str
    before_state: str
    after_state: str
    transition_operator: str
    removal_test: str

    def complete(self) -> bool:
        return all(str(value).strip() for value in asdict(self).values())


@dataclass(frozen=True)
class ConceptOutput:
    """Engineering capability: candidate outputs are auditable and structured."""

    title: str
    field: str
    core_mechanism: str
    operating_principle: str
    invariant: InvariantDeclaration | None = None
    novelty_delta: str = ""
    feasibility_risks: list[str] = field(default_factory=list)
    rejection_checks: list[str] = field(default_factory=list)

    def public_summary(self) -> dict:
        data = asdict(self)
        data["core_mechanism"] = self.core_mechanism[:500]
        data["operating_principle"] = self.operating_principle[:500]
        return data


if __name__ == "__main__":
    concept = ConceptOutput(
        title="Public demo concept",
        field="Generic engineering",
        core_mechanism="A constraint changes the admissible state set.",
        operating_principle="The useful behavior disappears when the constraint is removed.",
        invariant=InvariantDeclaration(
            invariant_claim="Connectivity class changes.",
            invariant_definition="Number of connected regions in a state graph.",
            before_state="Two regions.",
            after_state="One region.",
            transition_operator="Apply boundary constraint.",
            removal_test="Removing the boundary restores two regions.",
        ),
    )
    assert concept.invariant and concept.invariant.complete()
