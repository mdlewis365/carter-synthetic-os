# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from sos.governance import (
    GateDecision,
    GovernanceGate,
    GovernanceStatus,
    RiskLevel,
    ToolBoundary,
    ToolSpec,
    combine_decisions,
)
from sos.logging import EventRecorder, LifecycleMonitor
from sos.orchestration import (
    ContextBlock,
    assemble_context,
    context_anchor,
    normalize_request,
    run_pipeline,
    temporal_anchor,
)
from sos.registry import default_registry

pytestmark = pytest.mark.unit


def test_normalize_request_is_bounded_clean_and_reproducible() -> None:
    payload = {
        "text": "  synthetic\x00 request  ",
        "session_id": "session",
        "created_at": "2026-01-02T03:04:05Z",
    }
    first = normalize_request(payload)
    second = normalize_request(payload)

    assert first == second
    assert first.text == "synthetic request"
    assert len(first.request_id) == 24
    assert first.created_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_context_assembly_orders_priority_and_drops_whole_oversize_blocks() -> None:
    request = normalize_request("synthetic request", session_id="session")
    context = assemble_context(
        request,
        blocks=[
            ContextBlock("later", "small", priority=20),
            ContextBlock("first", "important", priority=1),
            ContextBlock("oversize", "x" * 2_000, priority=30),
        ],
        max_chars=600,
    )

    assert [block.name for block in context.blocks] == ["first", "later"]
    assert context.truncated is True
    assert "[oversize]" not in context.render()


def test_temporal_and_context_anchors_are_explicit_and_nonidentifying() -> None:
    temporal = temporal_anchor(now=datetime(2026, 1, 1, tzinfo=UTC), timezone_name="UTC")
    contextual = context_anchor("private-session-value", turn_index=2, labels=["test"])

    assert "2026-01-01" in temporal.render()
    assert "private-session-value" not in contextual.render()
    assert contextual.turn_index == 2


def test_governance_gate_blocks_unknown_tools_and_routes_high_risk_to_review() -> None:
    gate = GovernanceGate(allowed_tools={"math.evaluate"})

    denied = gate.evaluate_request("calculate", requested_tools={"shell.execute"})
    reviewed = gate.evaluate_request("calculate", risk_level=RiskLevel.HIGH)
    allowed = gate.evaluate_request("calculate", requested_tools={"math.evaluate"})

    assert denied.status is GovernanceStatus.BLOCK
    assert denied.metadata["denied_tools"] == ("shell.execute",)
    assert reviewed.status is GovernanceStatus.REVIEW
    assert reviewed.requires_human_review is True
    assert allowed.status is GovernanceStatus.ALLOW


def test_combined_governance_uses_most_restrictive_status() -> None:
    decision = combine_decisions(
        [
            GateDecision(GovernanceStatus.ALLOW),
            GateDecision(GovernanceStatus.REVIEW, ("review",), True),
            GateDecision(GovernanceStatus.BLOCK, ("blocked",)),
        ]
    )

    assert decision.status is GovernanceStatus.BLOCK
    assert decision.reasons == ("review", "blocked")


def test_tool_boundary_is_default_deny_and_redacts_handler_failure() -> None:
    boundary = ToolBoundary(allowlist={"math.add", "unsafe.fail"})
    boundary.register(ToolSpec("math.add", lambda left, right: left + right))
    boundary.register(
        ToolSpec("unsafe.fail", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("secret")))
    )
    boundary.register(ToolSpec("not.allowed", lambda: True))

    assert boundary.invoke("math.add", {"left": 2, "right": 3}).value == 5
    assert boundary.invoke("not.allowed").error_code == "tool_not_allowlisted"
    assert boundary.invoke("unknown").error_code == "unknown_tool"
    assert boundary.invoke("unsafe.fail", {"password": "do-not-echo"}).error_code == (
        "tool_execution_failed"
    )


def test_lcm_redacts_content_and_operation_report_contains_metadata_only() -> None:
    recorder = EventRecorder(id_factory=lambda: "event-1")
    event = recorder.record(
        "request.completed",
        session_id="private-session",
        metadata={
            "prompt": "private prompt",
            "api_token": "private token",
            "input_hash": "a" * 64,
            "provider": "mock",
        },
    )
    rendered = event.to_json()

    assert event.metadata["prompt"] == "[REDACTED]"
    assert event.metadata["api_token"] == "[REDACTED]"
    assert event.metadata["input_hash"] == "a" * 64
    assert "private prompt" not in rendered
    assert "private-session" not in rendered

    monitor = LifecycleMonitor(recorder)
    report = monitor.operation_report(generated_at=datetime(2026, 1, 1, tzinfo=UTC))
    assert report.event_count == 1
    assert "private" not in report.to_json()


def test_mock_pipeline_runs_end_to_end_without_persistence_or_network() -> None:
    recorder = EventRecorder(id_factory=iter(["accepted", "completed"]).__next__)
    result = run_pipeline("synthetic pipeline case", recorder=recorder)

    assert result.governance.status is GovernanceStatus.ALLOW
    assert result.response is not None
    assert result.response.provider == "mock"
    assert result.event_ids == ("accepted", "completed")
    serialized_events = "".join(event.to_json() for event in recorder.snapshot())
    assert "synthetic pipeline case" not in serialized_events


def test_default_registry_is_declarative() -> None:
    registry = default_registry()

    assert registry.get("provider.mock").deterministic is True
    assert registry.get("ams.sqlite").persistence == "opt-in"
    assert registry.get("provider.ollama").network == "loopback"


def test_utc_temporal_anchor_does_not_require_zoneinfo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sos.orchestration import anchors as anchors_module

    def fail_lookup(name: str):
        raise AssertionError(f"ZoneInfo must not be called for {name}")

    monkeypatch.setattr(anchors_module, "ZoneInfo", fail_lookup)
    anchor = temporal_anchor(
        now=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        timezone_name="UTC",
    )

    assert anchor.captured_at_utc == "2026-01-02T03:04:05Z"
    assert anchor.local_time == "2026-01-02T03:04:05+00:00"
    assert anchor.timezone_name == "UTC"
    assert anchor.render() == (
        "Time anchor: 2026-01-02T03:04:05+00:00 (UTC); UTC 2026-01-02T03:04:05Z."
    )


def test_non_utc_temporal_anchor_preserves_unknown_timezone_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from zoneinfo import ZoneInfoNotFoundError

    from sos.orchestration import anchors as anchors_module

    def unavailable(name: str):
        raise ZoneInfoNotFoundError(name)

    monkeypatch.setattr(anchors_module, "ZoneInfo", unavailable)

    with pytest.raises(ValueError, match=r"^unknown timezone: Missing/Zone$"):
        temporal_anchor(
            now=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
            timezone_name="Missing/Zone",
        )


def test_non_utc_temporal_anchor_still_uses_valid_named_zone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sos.orchestration import anchors as anchors_module

    lookups: list[str] = []

    def valid_zone(name: str):
        lookups.append(name)
        return timezone(timedelta(hours=-5))

    monkeypatch.setattr(anchors_module, "ZoneInfo", valid_zone)
    anchor = temporal_anchor(
        now=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        timezone_name="Test/Valid",
    )

    assert lookups == ["Test/Valid"]
    assert anchor.captured_at_utc == "2026-01-02T03:04:05Z"
    assert anchor.local_time == "2026-01-01T22:04:05-05:00"
    assert anchor.timezone_name == "Test/Valid"


def test_temporal_anchor_still_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match=r"^now must include timezone information$"):
        temporal_anchor(now=datetime(2026, 1, 2, 3, 4, 5), timezone_name="UTC")
