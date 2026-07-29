# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from carter.web import create_app
from csc.wav import encode_pcm16
from shared.config import load_settings
from sos.models import ProviderError

pytestmark = pytest.mark.integration


@pytest.fixture
def app():
    return create_app(load_settings({}), testing=True)


@pytest.fixture
def client(app):
    return app.test_client()


def authorize(client) -> tuple[dict[str, str], dict]:
    response = client.get("/api/session")
    data = response.get_json()
    return {"X-CSRF-Token": data["csrf_token"]}, data


def test_secret_free_startup_and_health(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "provider": "mock",
        "network_checked": False,
        "status": "ok",
        "version": "0.1.0",
    }


def test_secure_cookie_configuration_reaches_flask() -> None:
    app = create_app(
        load_settings({"CARTER_SESSION_COOKIE_SECURE": "true"}),
        testing=True,
    )

    assert app.config["SESSION_COOKIE_SECURE"] is True


def test_session_discloses_sensory_cloud_boundary_before_activation(client) -> None:
    data = client.get("/api/session").get_json()

    assert data["transcription_provider"] == "disabled"
    assert data["audio_cloud_transfer"] is False
    assert data["session_idle_ttl_seconds"] == 3600
    assert data["model_configured"] is True


def test_session_omits_configured_model_identifier() -> None:
    model_identifier = "synthetic-private-model-identifier"
    app = create_app(
        load_settings({"CARTER_DEFAULT_MODEL": model_identifier}),
        testing=True,
    )

    client = app.test_client()
    headers, data = authorize(client)
    chat = client.post(
        "/api/chat",
        json={"prompt": "Run a synthetic model-metadata minimization check."},
        headers=headers,
    ).get_json()
    stream = client.post(
        "/api/chat/stream",
        json={"prompt": "Run a synthetic streaming metadata minimization check."},
        headers=headers,
    ).get_data(as_text=True)

    assert "model" not in data
    assert data["model_configured"] is True
    assert model_identifier not in repr(data)
    assert "model" not in chat["provider"]
    assert chat["provider"]["model_configured"] is True
    assert model_identifier not in repr(chat)
    assert model_identifier not in stream


def test_interactive_interface_contains_legal_and_source_notices(client) -> None:
    page = client.get("/").get_data(as_text=True)

    assert "AGPL-3.0-only" in page
    assert "no warranty" in page
    assert "https://github.com/mdlewis365/carter-synthetic-os" in page
    assert "Source Code" in page


def test_license_route_displays_official_agpl_text(client) -> None:
    page = client.get("/license").get_data(as_text=True)

    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in page
    assert "Version 3, 19 November 2007" in page


@pytest.mark.parametrize(
    "path",
    [
        "/api/chat",
        "/api/eas/run",
        "/api/sis/run",
        "/api/csc/hearing",
        "/api/csc/camera",
        "/api/csc/transcript",
        "/api/csc/audio",
        "/api/csc/interpret",
        "/api/csc/clear",
        "/api/csc/tts",
        "/api/csc/playback",
        "/api/session/clear",
    ],
)
def test_state_changing_routes_require_csrf(client, path: str) -> None:
    response = client.post(path, json={})

    assert response.status_code == 403
    assert response.get_json()["error"] == "csrf_validation_failed"


def test_missing_chat_prompt_returns_bounded_client_error(client) -> None:
    headers, _ = authorize(client)

    response = client.post("/api/chat", json={}, headers=headers)

    assert response.status_code == 400
    assert response.get_json()["error"] == "prompt_is_required"


def test_mock_chat_is_deterministic_and_not_labeled_as_model(client) -> None:
    headers, _ = authorize(client)
    payload = {"prompt": "Run the synthetic public demonstration."}

    first = client.post("/api/chat", json=payload, headers=headers).get_json()
    second = client.post("/api/chat", json=payload, headers=headers).get_json()

    assert first["response"] == second["response"]
    assert first["provider"]["name"] == "mock"
    assert first["provider"]["probabilistic"] is False
    assert first["provider"]["metadata"]["language_model_invoked"] is False
    assert first["memory"]["persistent"] is False


def test_eas_job_is_owned_by_creating_session(app) -> None:
    owner = app.test_client()
    other = app.test_client()
    headers, _ = authorize(owner)
    result = owner.post(
        "/api/eas/run",
        json={
            "fixture_id": "synthetic_thermal_enclosure_v1",
            "problem_statement": "Evaluate the synthetic fixture.",
            "mode": "review-design",
        },
        headers=headers,
    ).get_json()

    assert owner.get("/api/jobs/" + result["job_id"]).status_code == 200
    assert other.get("/api/jobs/" + result["job_id"]).status_code == 404


def test_eas_and_sis_execute_without_cloud_credentials(client) -> None:
    headers, _ = authorize(client)
    eas = client.post(
        "/api/eas/run",
        json={
            "fixture_id": "synthetic_thermal_enclosure_v1",
            "problem_statement": "Evaluate the synthetic fixture.",
            "mode": "review-design",
        },
        headers=headers,
    ).get_json()
    sis = client.post(
        "/api/sis/run",
        json={
            "fixture_id": "synthetic_inspection_scheduler_v1",
            "problem_statement": "Generate a synthetic inspection candidate.",
            "mode": "system-architecture",
        },
        headers=headers,
    ).get_json()

    assert eas["status"] == "advisory_ready"
    assert eas["computation"]["result"]["status"] == "computed"
    assert eas["governance"]["governance_status"] == "needs_human_review"
    assert sis["status"] == "hypothesis_requires_independent_review"
    assert sis["human_review_required"] is True


def test_csc_state_and_transcript_are_session_isolated(app) -> None:
    first = app.test_client()
    second = app.test_client()
    first_headers, _ = authorize(first)
    authorize(second)
    first.post(
        "/api/csc/hearing",
        json={"active": True},
        headers=first_headers,
    )
    event = first.post(
        "/api/csc/transcript",
        json={
            "transcript": "Carter, classify the synthetic fixture.",
            "speech_detected": True,
        },
        headers=first_headers,
    ).get_json()

    assert event["event"]["attention"] == "focused"
    assert event["state"]["event_count"] == 1
    assert second.get("/api/csc/state").get_json()["state"]["event_count"] == 0


def test_synthetic_transcript_route_does_not_activate_microphone(client) -> None:
    headers, _ = authorize(client)

    response = client.post(
        "/api/csc/transcript",
        json={"transcript": "Carter, inspect the synthetic fixture."},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.get_json()["state"]["hearing_active"] is False


def test_audio_is_validated_and_discarded_when_transcription_disabled(client) -> None:
    headers, _ = authorize(client)
    client.post("/api/csc/hearing", json={"active": True}, headers=headers)
    audio = encode_pcm16([0.0] * 160, sample_rate_hz=16000)

    response = client.post(
        "/api/csc/audio",
        data=audio,
        headers=headers,
        content_type="audio/wav",
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["transcription"]["status"] == "skipped"
    assert data["transcription"]["data_sent_to_cloud"] is False
    assert data["raw_audio_retained"] is False
    assert data["event"] is None


def test_audio_route_rejects_multipart_to_prevent_temp_file_spooling(client) -> None:
    headers, _ = authorize(client)
    client.post("/api/csc/hearing", json={"active": True}, headers=headers)

    response = client.post(
        "/api/csc/audio",
        data={"audio": (b"synthetic", "synthetic.wav")},
        headers=headers,
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "audio_wav_body_required"


def test_camera_activation_requires_local_preview_declaration(client) -> None:
    headers, _ = authorize(client)

    rejected = client.post("/api/csc/camera", json={"active": True}, headers=headers)
    accepted = client.post(
        "/api/csc/camera",
        json={"active": True, "local_preview_only": True},
        headers=headers,
    )

    assert rejected.status_code == 400
    assert accepted.get_json()["frames_received_by_server"] is False


def test_tts_fails_before_network_without_configuration(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)
    headers, _ = authorize(client)

    response = client.post(
        "/api/csc/tts",
        json={"text": "Synthetic speech fixture."},
        headers=headers,
    )

    assert response.status_code == 503
    assert response.get_json()["error_code"] == "missing_elevenlabs_api_key"


def test_playback_state_is_session_scoped(client) -> None:
    headers, _ = authorize(client)

    active = client.post("/api/csc/playback", json={"active": True}, headers=headers).get_json()
    inactive = client.post("/api/csc/playback", json={"active": False}, headers=headers).get_json()

    assert active["voice"]["is_speaking"] is True
    assert inactive["voice"]["is_speaking"] is False


def test_clear_session_removes_playback_state(client) -> None:
    headers, _ = authorize(client)
    client.post("/api/csc/playback", json={"active": True}, headers=headers)

    response = client.post("/api/session/clear", json={}, headers=headers)

    assert response.status_code == 200
    assert client.get("/api/csc/state").get_json()["voice"]["is_speaking"] is False


def test_status_never_exposes_secret(client) -> None:
    status = client.get("/api/status").get_json()

    assert "flask_secret_key" not in repr(status)
    assert status["configuration"]["secret_mode"] == "ephemeral"
    assert status["license"] == "AGPL-3.0-only"


class FailingProvider:
    name = "failing-test-provider"

    def generate(self, request):
        raise ProviderError(
            "synthetic provider failure",
            provider=self.name,
            code="synthetic_failure",
        )

    def stream(self, request):
        raise ProviderError(
            "synthetic provider failure",
            provider=self.name,
            code="synthetic_failure",
        )
        yield ""


def test_provider_failure_is_sanitized() -> None:
    app = create_app(
        load_settings({"CARTER_DEFAULT_MODEL": "synthetic-test-model"}),
        provider=FailingProvider(),
        testing=True,
    )
    client = app.test_client()
    headers, _ = authorize(client)

    response = client.post(
        "/api/chat",
        json={"prompt": "Synthetic failure case"},
        headers=headers,
    )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "synthetic_failure",
        "provider": "failing-test-provider",
        "retryable": False,
    }


@pytest.mark.parametrize(
    ("route", "workflow_module_name", "patched_name", "payload", "expected_error"),
    [
        (
            "/api/eas/run",
            "eas.workflow",
            "normalize_request",
            {"mode": "review-design", "problem_statement": "Synthetic request."},
            "Engineering mode is not supported.",
        ),
        (
            "/api/sis/run",
            "sis.workflow",
            "normalize_mode",
            {"mode": "system-architecture", "problem_statement": "Synthetic request."},
            "Invention mode is not supported.",
        ),
    ],
)
def test_workflow_responses_do_not_expose_exception_details(
    client,
    monkeypatch: pytest.MonkeyPatch,
    route: str,
    workflow_module_name: str,
    patched_name: str,
    payload: dict,
    expected_error: str,
) -> None:
    exception_detail = "UNIQUE-WEB-SENTINEL C:\\private\\provider\\sentinel.txt"

    def fail(*_args, **_kwargs):
        raise ValueError(exception_detail)

    workflow_module = __import__(workflow_module_name, fromlist=[patched_name])
    monkeypatch.setattr(workflow_module, patched_name, fail)
    headers, _ = authorize(client)
    response = client.post(route, json=payload, headers=headers)
    response_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.get_json()["errors"] == [expected_error]
    assert "UNIQUE-WEB-SENTINEL" not in response_text
    assert "C:\\private\\provider\\sentinel.txt" not in response_text
