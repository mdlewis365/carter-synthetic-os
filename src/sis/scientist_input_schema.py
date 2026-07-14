# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
# Public-safe excerpt adapted from the private implementation.
"""Scientist input schema for a bounded ideation workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class MetaGuidance:
    search_forcing_function: str = "representation_shift"
    structural_lens: str = "graph_topology"
    discovery_mode: str = "transform_first"
    causal_necessity_condition: str = "constraint_must_be_necessary"
    prior_art_collapse_pattern: str = "reject_parameter_tuning"


@dataclass(frozen=True)
class ScientistInput:
    """Engineering capability: structure creative input before generation."""

    invention_mode: str
    exploration_vector: str
    domain: str
    framing: str
    allowed_approaches: list[str] = field(default_factory=list)
    rejection_boundaries: list[str] = field(default_factory=list)
    meta_guidance: MetaGuidance = field(default_factory=MetaGuidance)

    def validate(self) -> list[str]:
        errors = []
        for field_name in ("invention_mode", "exploration_vector", "domain", "framing"):
            if not str(getattr(self, field_name) or "").strip():
                errors.append(f"missing:{field_name}")
        if not self.rejection_boundaries:
            errors.append("missing:rejection_boundaries")
        return errors

    def public_payload(self) -> dict:
        """Returns schema fields only, never private prompt text."""

        return asdict(self)


if __name__ == "__main__":
    request = ScientistInput(
        invention_mode="mechanism-discovery",
        exploration_vector="Use a constraint as the enabling mechanism.",
        domain="Thermal transport",
        framing="Find a falsifiable mechanism-level concept.",
        rejection_boundaries=["Reject simple parameter tuning."],
    )
    assert request.validate() == []
