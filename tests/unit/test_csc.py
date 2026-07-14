# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json
from io import BytesIO

import pytest

from csc.interpretation import normalize_interpretation
from csc.state import SensorySessionStore, classify_attention
from csc.transcription import (
    DisabledTranscriber,
    GoogleTranscriber,
    _json_object,
    _normalize,
)
from csc.tts import VoiceBoundary
from csc.wav import encode_pcm16, validate_wav

pytestmark = [pytest.mark.unit, pytest.mark.sensory]


@pytest.mark.parametrize(
    ("transcript", "speech", "speaking", "expected"),
    [
        ("Carter, review this", True, False, "focused"),
        ("the pump is running", True, False, "peripheral"),
        ("Carter, wait", True, True, "ignored"),
        ("", False, False, "background"),
    ],
)
def test_attention_classification(
    transcript: str, speech: bool, speaking: bool, expected: str
) -> None:
    assert (
        classify_attention(
            transcript,
            speech_detected=speech,
            carter_is_speaking=speaking,
        )
        == expected
    )


def test_hearing_requires_explicit_session_activation() -> None:
    store = SensorySessionStore()

    with pytest.raises(PermissionError):
        store.add_transcript("session-a", "Carter, hello")


def test_transcripts_and_interpretations_are_session_isolated() -> None:
    store = SensorySessionStore()
    store.set_hearing("session-a", True)
    store.set_hearing("session-b", True)
    store.add_transcript("session-a", "Carter, inspect the synthetic fixture")
    store.set_interpretation("session-a", {"priority": "focused"})

    assert store.snapshot("session-a")["event_count"] == 1
    assert store.snapshot("session-b")["event_count"] == 0
    assert store.snapshot("session-b")["latest_interpretation"] is None


def test_microphone_and_camera_activation_are_independent() -> None:
    store = SensorySessionStore()
    store.set_camera("session", True)

    state = store.set_hearing("session", False)

    assert state["hearing_active"] is False
    assert state["camera_active"] is True


def test_synthetic_transcript_does_not_require_or_enable_microphone() -> None:
    store = SensorySessionStore()

    event = store.add_transcript(
        "session",
        "Carter, inspect the synthetic fixture.",
        source="synthetic_text_fixture",
        require_hearing=False,
    )

    assert event.attention == "focused"
    assert store.snapshot("session")["hearing_active"] is False


def test_sensory_state_discloses_non_retention() -> None:
    state = SensorySessionStore().snapshot("session")

    assert state["raw_audio_retained"] is False
    assert state["camera_frames_retained"] is False
    assert state["persistence"] == "memory_only"
    assert state["requires_explicit_activation"] is True


def test_rolling_buffer_is_bounded() -> None:
    now = [100.0]
    store = SensorySessionStore(
        window_seconds=10,
        max_events=2,
        clock=lambda: now[0],
    )
    store.set_hearing("session", True)
    store.add_transcript("session", "one")
    now[0] += 1
    store.add_transcript("session", "two")
    now[0] += 1
    store.add_transcript("session", "three")

    context = store.context("session")

    assert [event["transcript"] for event in context["events"]] == ["two", "three"]


def test_sensory_session_expires_after_idle_ttl() -> None:
    now = [100.0]
    store = SensorySessionStore(
        session_ttl_seconds=10,
        clock=lambda: now[0],
    )
    store.add_transcript(
        "session",
        "Carter, synthetic expiring event.",
        require_hearing=False,
    )
    now[0] += 11

    state = store.snapshot("session")

    assert state["event_count"] == 0
    assert state["hearing_active"] is False
    assert state["camera_active"] is False


def test_wav_encoder_and_validator_round_trip() -> None:
    audio = encode_pcm16([0.0, 0.25, -0.25, 1.0, -1.0], sample_rate_hz=16000)

    metadata = validate_wav(audio)

    assert metadata.channels == 1
    assert metadata.sample_width_bytes == 2
    assert metadata.sample_rate_hz == 16000
    assert metadata.frame_count == 5


def test_invalid_wav_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid_wav_header"):
        validate_wav(b"not audio")


def test_interpretation_cannot_focus_non_wake_speech() -> None:
    context = {
        "events": [
            {
                "transcript": "ambient synthetic speech",
                "attention": "peripheral",
                "wake_name_detected": False,
            }
        ]
    }
    provider_value = {
        "semantic_complete": True,
        "priority": "focused",
        "utterance_type": "direct_address",
        "candidate_response_needed": True,
        "recommended_next_step": "prepare_candidate_response",
        "confidence": 0.9,
    }

    result = normalize_interpretation(provider_value, buffer_context=context, backend="test")

    assert result["addressing_carter"] is False
    assert result["priority"] == "peripheral"
    assert result["candidate_response_needed"] is False
    assert result["authorizes_response"] is False


def test_interpretation_recognizes_governed_direct_address() -> None:
    context = {
        "events": [
            {
                "transcript": "Carter, summarize this synthetic case.",
                "attention": "focused",
                "wake_name_detected": True,
            }
        ]
    }
    result = normalize_interpretation(
        {
            "semantic_complete": True,
            "priority": "focused",
            "candidate_response_needed": True,
            "recommended_next_step": "prepare_candidate_response",
            "confidence": 0.8,
        },
        buffer_context=context,
        backend="test",
    )

    assert result["addressing_carter"] is True
    assert result["utterance_type"] == "direct_address"
    assert result["candidate_response_needed"] is True
    assert result["authorizes_response"] is False


@pytest.mark.parametrize("confidence", [float("nan"), float("inf"), float("-inf"), "NaN"])
def test_interpretation_normalizes_nonfinite_confidence(confidence: object) -> None:
    context = {
        "events": [
            {
                "transcript": "ambient synthetic speech",
                "attention": "peripheral",
                "wake_name_detected": False,
            }
        ]
    }

    result = normalize_interpretation(
        {"confidence": confidence},
        buffer_context=context,
        backend="test",
    )

    assert result["confidence"] == 0.0


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_interpretation_rejects_nonfinite_json_constants(constant: str) -> None:
    with pytest.raises(ValueError, match="nonfinite_json_constant"):
        normalize_interpretation(
            f'{{"confidence": {constant}}}',
            buffer_context={"events": []},
            backend="test",
        )


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_transcription_rejects_nonfinite_json_constants(constant: str) -> None:
    with pytest.raises(ValueError, match="nonfinite_json_constant"):
        _json_object(f'{{"confidence": {constant}}}')


@pytest.mark.parametrize("confidence", [float("nan"), float("inf"), float("-inf"), "NaN"])
def test_transcription_and_store_drop_nonfinite_confidence(confidence: object) -> None:
    transcription = _normalize({"transcript": "synthetic", "confidence": confidence}, "test")
    store = SensorySessionStore()
    event = store.add_transcript(
        "session",
        "synthetic",
        confidence=confidence,
        require_hearing=False,
    )

    assert transcription.confidence is None
    assert event.confidence is None


def test_transcription_is_disabled_without_cloud_configuration() -> None:
    result = DisabledTranscriber().transcribe(b"synthetic", "audio/wav")

    assert result.status == "skipped"
    assert result.data_sent_to_cloud is False


def test_google_transcriber_fails_before_network_without_key() -> None:
    result = GoogleTranscriber(api_key="").transcribe(b"synthetic", "audio/wav")

    assert result.error_code == "missing_google_api_key"
    assert result.data_sent_to_cloud is False


def test_voice_status_exposes_no_voice_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "synthetic-placeholder")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "synthetic-voice-placeholder")

    status = VoiceBoundary().status("session")

    assert status["api_key_configured"] is True
    assert status["voice_id_configured"] is True
    assert "synthetic-placeholder" not in repr(status)
    assert "synthetic-voice-placeholder" not in repr(status)


def test_voice_session_can_be_removed() -> None:
    voice = VoiceBoundary()
    voice.mark_speaking("session", True)

    voice.remove_session("session")

    assert voice.is_speaking("session") is False


def test_elevenlabs_request_uses_query_output_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    seen: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data)
        seen["timeout"] = timeout
        return FakeResponse(b"synthetic-mp3")

    monkeypatch.setenv("ELEVENLABS_API_KEY", "synthetic-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "synthetic voice/id")
    monkeypatch.setattr("csc.tts.urllib.request.urlopen", fake_urlopen)

    result = VoiceBoundary().synthesize("Synthetic speech fixture.")

    assert result.success is True
    assert seen["url"].endswith("/synthetic%20voice%2Fid/stream?output_format=mp3_44100_128")
    assert "output_format" not in seen["body"]
    assert seen["timeout"] == 30
