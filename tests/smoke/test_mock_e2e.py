# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from carter.web import create_app
from shared.config import load_settings

pytestmark = pytest.mark.smoke


def test_mock_mode_continuous_public_experience() -> None:
    client = create_app(load_settings({}), testing=True).test_client()
    session = client.get("/api/session").get_json()
    headers = {"X-CSRF-Token": session["csrf_token"]}

    chat = client.post(
        "/api/chat",
        json={"prompt": "Run a synthetic governed request."},
        headers=headers,
    )
    eas = client.post(
        "/api/eas/run",
        json={
            "fixture_id": "synthetic_thermal_enclosure_v1",
            "problem_statement": "Evaluate the synthetic enclosure fixture.",
            "mode": "review-design",
        },
        headers=headers,
    )
    sis = client.post(
        "/api/sis/run",
        json={
            "fixture_id": "synthetic_inspection_scheduler_v1",
            "problem_statement": "Generate a synthetic inspection candidate.",
            "mode": "system-architecture",
        },
        headers=headers,
    )
    hearing = client.post("/api/csc/hearing", json={"active": True}, headers=headers)
    transcript = client.post(
        "/api/csc/transcript",
        json={
            "transcript": "Carter, inspect the synthetic evidence.",
            "speech_detected": True,
        },
        headers=headers,
    )
    interpretation = client.post("/api/csc/interpret", json={}, headers=headers)

    assert chat.status_code == 200
    assert eas.get_json()["computation"]["result"]["status"] == "computed"
    assert sis.get_json()["status"] == "hypothesis_requires_independent_review"
    assert hearing.get_json()["state"]["hearing_active"] is True
    assert transcript.get_json()["event"]["attention"] == "focused"
    assert interpretation.get_json()["interpretation"]["governed"] is True
    assert interpretation.get_json()["interpretation"]["authorizes_response"] is False
