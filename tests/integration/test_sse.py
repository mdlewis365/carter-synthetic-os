# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json

import pytest

from carter.web import create_app
from shared.config import load_settings

pytestmark = pytest.mark.integration


def test_sse_stream_has_metadata_tokens_and_completion() -> None:
    client = create_app(load_settings({}), testing=True).test_client()
    session = client.get("/api/session").get_json()

    response = client.post(
        "/api/chat/stream",
        json={"prompt": "Stream the deterministic synthetic fixture."},
        headers={"X-CSRF-Token": session["csrf_token"]},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert response.headers["X-Accel-Buffering"] == "no"
    assert "event: metadata" in body
    assert "event: token" in body
    assert "event: done" in body
    assert "Mock provider" in body


def test_sse_data_lines_are_valid_json() -> None:
    client = create_app(load_settings({}), testing=True).test_client()
    session = client.get("/api/session").get_json()
    body = client.post(
        "/api/chat/stream",
        json={"prompt": "Validate SSE framing."},
        headers={"X-CSRF-Token": session["csrf_token"]},
    ).get_data(as_text=True)

    data_lines = [line[6:] for line in body.splitlines() if line.startswith("data: ")]

    assert data_lines
    assert all(isinstance(json.loads(line), dict) for line in data_lines)
