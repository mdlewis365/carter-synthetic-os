# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Secure-by-default Flask application for the public research release."""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    session,
    stream_with_context,
)

from csc.interpretation import interpret_buffer
from csc.state import SensorySessionStore
from csc.transcription import create_transcriber
from csc.tts import VoiceBoundary
from csc.wav import MAX_AUDIO_BYTES, validate_wav
from eas.workflow import EngineeringWorkflow
from shared.config import Settings, load_settings
from shared.version import __version__
from sis.workflow import IdeationWorkflow
from sos.models import ProviderError, available_providers
from sos.registry import default_registry

from .identity import identity_metadata
from .jobs import JobStore
from .runtime import CarterRuntime

SOURCE_URL = "https://github.com/mdlewis365/carter-synthetic-os"
PACKAGED_LICENSE = Path(__file__).resolve().parent / "legal" / "LICENSE"
PACKAGED_EVIDENCE_MANIFEST = Path(__file__).resolve().parent / "evidence" / "manifest.json"


def _session_context() -> tuple[str, str]:
    if "session_id" not in session:
        session["session_id"] = secrets.token_urlsafe(24)
        session["csrf_token"] = secrets.token_urlsafe(32)
    return str(session["session_id"]), str(session["csrf_token"])


def _require_csrf(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        _, expected = _session_context()
        supplied = request.headers.get("X-CSRF-Token", "")
        if not supplied or not secrets.compare_digest(expected, supplied):
            return jsonify({"error": "csrf_validation_failed"}), 403
        return view(*args, **kwargs)

    return wrapped


def _json_body(*, max_chars: int = 100_000) -> dict[str, Any]:
    if not request.is_json:
        raise ValueError("application_json_required")
    data = request.get_json(silent=False)
    if not isinstance(data, dict):
        raise ValueError("json_object_required")
    if len(json.dumps(data, default=str)) > max_chars:
        raise ValueError("json_payload_too_large")
    return data


def _sse(event: str, payload: dict[str, Any]) -> str:
    compact = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"event: {event}\ndata: {compact}\n\n"


def create_app(
    settings: Settings | None = None,
    *,
    provider: Any | None = None,
    testing: bool = False,
) -> Flask:
    configured = settings or load_settings()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=configured.flask_secret_key,
        TESTING=testing,
        MAX_CONTENT_LENGTH=MAX_AUDIO_BYTES + 64 * 1024,
        SESSION_COOKIE_NAME="carter_public_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=configured.session_idle_ttl_seconds,
        JSON_SORT_KEYS=True,
    )

    runtime = CarterRuntime(configured, provider=provider)
    sensory = SensorySessionStore(
        window_seconds=configured.csc_buffer_seconds,
        max_events=configured.csc_buffer_max_events,
        session_ttl_seconds=configured.session_idle_ttl_seconds,
    )
    voice = VoiceBoundary()
    transcriber = create_transcriber(configured.csc_transcription_provider)
    engineering = EngineeringWorkflow()
    ideation = IdeationWorkflow()
    jobs = JobStore(ttl_seconds=min(900, configured.session_idle_ttl_seconds))

    app.extensions["carter_settings"] = configured
    app.extensions["carter_runtime"] = runtime
    app.extensions["carter_sensory"] = sensory
    app.extensions["carter_voice"] = voice
    app.extensions["carter_transcriber"] = transcriber
    app.extensions["carter_jobs"] = jobs

    @app.after_request
    def security_headers(response: Response) -> Response:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; "
            "form-action 'self'"
        )
        response.headers["Permissions-Policy"] = (
            "microphone=(self), camera=(self), geolocation=(), payment=()"
        )
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(413)
    def content_too_large(_: Any) -> tuple[Response, int]:
        return jsonify({"error": "request_too_large"}), 413

    @app.errorhandler(ProviderError)
    def provider_failure(exc: ProviderError) -> tuple[Response, int]:
        return (
            jsonify(
                {
                    "error": exc.code,
                    "provider": exc.provider,
                    "retryable": exc.retryable,
                }
            ),
            503,
        )

    @app.errorhandler(ValueError)
    def invalid_request(exc: ValueError) -> tuple[Response, int]:
        if request.path.startswith("/api/"):
            return jsonify({"error": str(exc)}), 400
        raise exc

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/license")
    def license_view() -> str:
        text = PACKAGED_LICENSE.read_text(encoding="utf-8")
        return render_template("license.html", license_text=text)

    @app.get("/health")
    def health() -> Response:
        return jsonify(
            {
                "status": "ok",
                "version": __version__,
                "provider": runtime.provider.name,
                "network_checked": False,
            }
        )

    @app.get("/api/session")
    def public_session() -> Response:
        session_id, csrf_token = _session_context()
        return jsonify(
            {
                "session_id": session_id,
                "csrf_token": csrf_token,
                "provider": runtime.provider.name,
                "model": configured.default_model,
                "mock": runtime.provider.name == "mock",
                "retention": "session_memory_only",
                "session_idle_ttl_seconds": configured.session_idle_ttl_seconds,
                "transcription_provider": configured.csc_transcription_provider,
                "audio_cloud_transfer": (configured.csc_transcription_provider == "google"),
            }
        )

    @app.get("/api/status")
    def status() -> Response:
        return jsonify(
            {
                "project": "Carter Synthetic OS",
                "version": __version__,
                "release": "Initial Public Research Release",
                "identity": identity_metadata(),
                "configuration": configured.public_dict(),
                "source_code": SOURCE_URL,
                "license": "AGPL-3.0-only",
                "components": [
                    {
                        "name": item.name,
                        "category": item.category,
                        "deterministic": item.deterministic,
                        "persistence": item.persistence,
                        "network": item.network,
                        "status": item.status,
                    }
                    for item in default_registry().list()
                ],
            }
        )

    @app.get("/api/providers")
    def providers() -> Response:
        return jsonify(
            {
                "available": available_providers(),
                "selected": runtime.provider.name,
                "default": "mock",
                "provider_imports_are_lazy": True,
            }
        )

    @app.post("/api/chat")
    @_require_csrf
    def chat() -> Response:
        session_id, _ = _session_context()
        body = _json_body(max_chars=10_000)
        prompt = body.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt_is_required")
        result = runtime.respond(session_id, prompt)
        return jsonify(result)

    @app.post("/api/chat/stream")
    @_require_csrf
    def chat_stream() -> Response:
        session_id, _ = _session_context()
        body = _json_body(max_chars=10_000)
        prompt = body.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt_is_required")

        @stream_with_context
        def generate() -> Any:
            for event in runtime.stream(session_id, prompt):
                event_name = str(event.pop("type", "message"))
                yield _sse(event_name, event)

        response = Response(generate(), mimetype="text/event-stream")
        response.headers["X-Accel-Buffering"] = "no"
        response.headers["Connection"] = "keep-alive"
        return response

    @app.post("/api/eas/run")
    @_require_csrf
    def eas_run() -> Response:
        session_id, _ = _session_context()
        body = _json_body()
        job = jobs.create(session_id, "eas")
        jobs.append_event(session_id, job.job_id, stage="stage_one", status="running")
        result = engineering.run(body, provider=runtime.workflow_provider)
        result["job_id"] = job.job_id
        jobs.complete(session_id, job.job_id, result)
        return jsonify(result)

    @app.post("/api/sis/run")
    @_require_csrf
    def sis_run() -> Response:
        session_id, _ = _session_context()
        body = _json_body()
        job = jobs.create(session_id, "sis")
        jobs.append_event(session_id, job.job_id, stage="candidate", status="running")
        result = ideation.run(body, provider=runtime.workflow_provider)
        result["job_id"] = job.job_id
        jobs.complete(session_id, job.job_id, result)
        return jsonify(result)

    @app.get("/api/jobs/<job_id>")
    def job_status(job_id: str) -> tuple[Response, int] | Response:
        session_id, _ = _session_context()
        try:
            job = jobs.get(session_id, job_id)
        except (KeyError, PermissionError):
            return jsonify({"error": "job_not_found"}), 404
        return jsonify(job.public_dict())

    def sensory_payload(session_id: str, **extra: Any) -> dict[str, Any]:
        return {
            "state": sensory.snapshot(session_id),
            "voice": voice.status(session_id),
            **extra,
        }

    @app.get("/api/csc/state")
    def csc_state() -> Response:
        session_id, _ = _session_context()
        return jsonify(sensory_payload(session_id))

    @app.post("/api/csc/hearing")
    @_require_csrf
    def csc_hearing() -> Response:
        session_id, _ = _session_context()
        body = _json_body(max_chars=2000)
        if not isinstance(body.get("active"), bool):
            raise ValueError("active_must_be_boolean")
        state = sensory.set_hearing(session_id, body["active"])
        return jsonify(sensory_payload(session_id, state=state))

    @app.post("/api/csc/camera")
    @_require_csrf
    def csc_camera() -> Response:
        session_id, _ = _session_context()
        body = _json_body(max_chars=2000)
        active = body.get("active")
        if not isinstance(active, bool):
            raise ValueError("active_must_be_boolean")
        if active and body.get("local_preview_only") is not True:
            raise ValueError("camera_is_local_preview_only")
        state = sensory.set_camera(session_id, active)
        return jsonify(
            sensory_payload(
                session_id,
                state=state,
                camera_boundary="browser_local_preview_only",
                frames_received_by_server=False,
            )
        )

    @app.post("/api/csc/transcript")
    @_require_csrf
    def csc_transcript() -> Response:
        session_id, _ = _session_context()
        body = _json_body(max_chars=5000)
        event = sensory.add_transcript(
            session_id,
            body.get("transcript"),
            speech_detected=body.get("speech_detected", True),
            confidence=body.get("confidence"),
            carter_is_speaking=voice.is_speaking(session_id),
            source="synthetic_text_fixture",
            require_hearing=False,
        )
        return jsonify(
            sensory_payload(
                session_id,
                event=event.public_dict(),
                buffer=sensory.context(session_id),
            )
        )

    @app.post("/api/csc/audio")
    @_require_csrf
    def csc_audio() -> Response:
        session_id, _ = _session_context()
        if not sensory.snapshot(session_id)["hearing_active"]:
            return jsonify({"error": "hearing_not_active"}), 409
        if request.mimetype not in {"audio/wav", "audio/x-wav"}:
            raise ValueError("audio_wav_body_required")
        # A bounded raw body avoids Werkzeug's multipart temporary-file spool.
        audio = request.get_data(cache=False, as_text=False, parse_form_data=False)
        if not audio:
            raise ValueError("audio_body_required")
        if len(audio) > MAX_AUDIO_BYTES:
            return jsonify({"error": "audio_too_large"}), 413
        metadata = validate_wav(audio)
        transcription = transcriber.transcribe(audio, "audio/wav")
        event = None
        if transcription.status in {"transcribed", "no_speech"}:
            event = sensory.add_transcript(
                session_id,
                transcription.transcript,
                speech_detected=transcription.speech_detected,
                confidence=transcription.confidence,
                carter_is_speaking=voice.is_speaking(session_id),
                source="browser_microphone",
            ).public_dict()
        return jsonify(
            sensory_payload(
                session_id,
                wav=metadata.to_dict(),
                transcription=transcription.to_dict(),
                event=event,
                raw_audio_retained=False,
            )
        )

    @app.post("/api/csc/interpret")
    @_require_csrf
    def csc_interpret() -> Response:
        session_id, _ = _session_context()
        _json_body(max_chars=1000)
        context = sensory.context(session_id)
        interpretation = interpret_buffer(
            context,
            backend=configured.csc_interpretation_backend,
            model=configured.csc_ollama_model or configured.ollama_model or None,
            settings={
                "base_url": configured.ollama_base_url,
                "allow_remote": configured.allow_remote_ollama,
            },
        )
        sensory.set_interpretation(session_id, interpretation)
        return jsonify(
            sensory_payload(
                session_id,
                interpretation=interpretation,
                buffer=sensory.context(session_id),
            )
        )

    @app.post("/api/csc/clear")
    @_require_csrf
    def csc_clear() -> Response:
        session_id, _ = _session_context()
        _json_body(max_chars=1000)
        state = sensory.clear(session_id)
        return jsonify(sensory_payload(session_id, state=state))

    @app.post("/api/csc/tts")
    @_require_csrf
    def csc_tts() -> tuple[Response, int] | Response:
        session_id, _ = _session_context()
        body = _json_body(max_chars=2000)
        result = voice.synthesize(body.get("text"))
        if not result.success or result.audio_bytes is None:
            return jsonify(result.public_dict()), 503
        response = Response(result.audio_bytes, mimetype=result.content_type)
        response.headers["Content-Disposition"] = "inline"
        response.headers["X-Carter-Session"] = session_id[:8]
        return response

    @app.post("/api/csc/playback")
    @_require_csrf
    def csc_playback() -> Response:
        session_id, _ = _session_context()
        body = _json_body(max_chars=1000)
        if not isinstance(body.get("active"), bool):
            raise ValueError("active_must_be_boolean")
        voice.mark_speaking(session_id, body["active"])
        return jsonify(sensory_payload(session_id))

    @app.post("/api/session/clear")
    @_require_csrf
    def clear_session() -> Response:
        session_id, _ = _session_context()
        runtime_result = runtime.clear_session(session_id)
        sensory.remove_session(session_id)
        voice.remove_session(session_id)
        removed_jobs = jobs.clear_owner(session_id)
        session.clear()
        return jsonify(
            {
                **runtime_result,
                "jobs_removed": removed_jobs,
                "session_cleared": True,
            }
        )

    @app.get("/api/evidence/manifest")
    def evidence_manifest() -> tuple[Response, int] | Response:
        if not PACKAGED_EVIDENCE_MANIFEST.is_file():
            return jsonify({"error": "evidence_not_generated"}), 404
        try:
            payload = json.loads(PACKAGED_EVIDENCE_MANIFEST.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return jsonify({"error": "evidence_manifest_invalid"}), 500
        return jsonify(payload)

    return app
