# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Deterministic governance gates.

These gates enforce declared structural and risk rules. They are not a
substitute for domain safety analysis, professional review, or content-policy
classification by a qualified operator.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class GovernanceStatus(StrEnum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class GateDecision:
    status: GovernanceStatus
    reasons: tuple[str, ...] = ()
    requires_human_review: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class GovernanceGate:
    """Apply explicit request-size, tool, and declared-risk rules."""

    def __init__(
        self,
        *,
        max_request_chars: int = 100_000,
        allowed_tools: Iterable[str] = (),
        block_critical: bool = True,
    ) -> None:
        if max_request_chars < 1:
            raise ValueError("max_request_chars must be positive")
        self.max_request_chars = max_request_chars
        self.allowed_tools = frozenset(str(name).strip() for name in allowed_tools)
        self.block_critical = block_critical

    def evaluate_request(
        self,
        text: str,
        *,
        risk_level: RiskLevel | str = RiskLevel.LOW,
        requested_tools: Iterable[str] = (),
        human_review_requested: bool = False,
    ) -> GateDecision:
        if not isinstance(text, str) or not text.strip():
            return GateDecision(GovernanceStatus.BLOCK, ("empty_request",))
        if len(text) > self.max_request_chars:
            return GateDecision(
                GovernanceStatus.BLOCK,
                ("request_size_limit_exceeded",),
                metadata={"character_count": len(text)},
            )
        try:
            risk = risk_level if isinstance(risk_level, RiskLevel) else RiskLevel(risk_level)
        except ValueError as exc:
            raise ValueError(f"unsupported risk level: {risk_level}") from exc

        tools = tuple(sorted({str(name).strip() for name in requested_tools if str(name).strip()}))
        denied = tuple(name for name in tools if name not in self.allowed_tools)
        if denied:
            return GateDecision(
                GovernanceStatus.BLOCK,
                ("tool_not_allowlisted",),
                metadata={"denied_tools": denied},
            )
        if risk is RiskLevel.CRITICAL and self.block_critical:
            return GateDecision(
                GovernanceStatus.BLOCK,
                ("declared_critical_risk",),
                True,
                {"risk_level": risk.value},
            )
        if risk in {RiskLevel.HIGH, RiskLevel.CRITICAL} or human_review_requested:
            reason = "declared_high_risk" if risk is RiskLevel.HIGH else "human_review_required"
            return GateDecision(
                GovernanceStatus.REVIEW,
                (reason,),
                True,
                {"risk_level": risk.value},
            )
        return GateDecision(
            GovernanceStatus.ALLOW,
            metadata={"risk_level": risk.value, "requested_tools": tools},
        )

    def evaluate_provider_result(
        self,
        *,
        provider_succeeded: bool,
        schema_valid: bool = True,
        deterministic_checks_passed: bool = True,
        advisory_domain: bool = False,
    ) -> GateDecision:
        reasons: list[str] = []
        if not provider_succeeded:
            return GateDecision(GovernanceStatus.BLOCK, ("provider_failed",))
        if not schema_valid:
            reasons.append("schema_validation_failed")
        if not deterministic_checks_passed:
            reasons.append("deterministic_check_failed")
        if reasons:
            return GateDecision(GovernanceStatus.BLOCK, tuple(reasons), True)
        if advisory_domain:
            return GateDecision(
                GovernanceStatus.REVIEW,
                ("professional_review_required",),
                True,
            )
        return GateDecision(GovernanceStatus.ALLOW)


def combine_decisions(decisions: Iterable[GateDecision]) -> GateDecision:
    """Combine independent gates using the most restrictive status."""

    values = tuple(decisions)
    if not values:
        return GateDecision(GovernanceStatus.ALLOW)
    rank = {
        GovernanceStatus.ALLOW: 0,
        GovernanceStatus.REVIEW: 1,
        GovernanceStatus.BLOCK: 2,
    }
    status = max((decision.status for decision in values), key=rank.__getitem__)
    reasons = tuple(dict.fromkeys(reason for decision in values for reason in decision.reasons))
    return GateDecision(
        status,
        reasons,
        any(decision.requires_human_review for decision in values),
        {"gate_count": len(values)},
    )
