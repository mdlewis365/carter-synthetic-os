# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Optional cloud transcription boundary. Audio is never written to disk."""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from .wav import validate_wav


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str | None
    speech_detected: bool | None
    wake_name_detected: bool
    confidence: float | None
    status: str
    error_code: str | None = None
    provider: str = "disabled"
    data_sent_to_cloud: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class Transcriber(Protocol):
    def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult: ...


class DisabledTranscriber:
    def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult:
        return TranscriptionResult(
            transcript=None,
            speech_detected=None,
            wake_name_detected=False,
            confidence=None,
            status="skipped",
            error_code="transcription_disabled",
        )


def _reject_nonfinite_json_constant(constant: str) -> object:
    raise ValueError(f"nonfinite_json_constant:{constant}")


def _json_object(text: str) -> dict[str, Any]:
    clean = re.sub(r"^\x60{3}(?:json)?\s*|\s*\x60{3}$", "", str(text).strip())
    try:
        value = json.loads(clean, parse_constant=_reject_nonfinite_json_constant)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, flags=re.DOTALL)
        if not match:
            raise ValueError("provider_response_not_json") from None
        value = json.loads(
            match.group(0),
            parse_constant=_reject_nonfinite_json_constant,
        )
    if not isinstance(value, dict):
        raise ValueError("provider_response_not_object")
    return value


def _normalize(value: dict[str, Any], provider: str) -> TranscriptionResult:
    transcript = " ".join(str(value.get("transcript") or "").split())[:2000] or None
    detected = value.get("speech_detected")
    if not isinstance(detected, bool):
        detected = None
    confidence = value.get("confidence")
    try:
        confidence = None if confidence is None else float(confidence)
        if confidence is not None and not math.isfinite(confidence):
            confidence = None
        elif confidence is not None:
            confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = None
    status = str(value.get("transcription_status") or "").lower()
    if status not in {"transcribed", "no_speech"}:
        status = "transcribed" if transcript else "no_speech"
    return TranscriptionResult(
        transcript=transcript,
        speech_detected=detected if detected is not None else bool(transcript),
        wake_name_detected=bool(re.search(r"\bcarter\b", transcript or "", flags=re.IGNORECASE)),
        confidence=confidence,
        status=status,
        provider=provider,
        data_sent_to_cloud=True,
    )


class GoogleTranscriber:
    """Gemini adapter. Constructing this class performs no import or network I/O."""

    def __init__(self, *, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key if api_key is not None else os.getenv("GOOGLE_API_KEY")
        self.model = model or os.getenv("GOOGLE_MODEL") or "gemini-2.5-flash"

    def transcribe(self, audio: bytes, mime_type: str) -> TranscriptionResult:
        if not self.api_key:
            return TranscriptionResult(
                None,
                None,
                False,
                None,
                "error",
                "missing_google_api_key",
                "google",
                False,
            )
        if mime_type not in {"audio/wav", "audio/x-wav"}:
            return TranscriptionResult(
                None,
                None,
                False,
                None,
                "error",
                "unsupported_audio_type",
                "google",
                False,
            )
        try:
            validate_wav(audio)
            from google import genai
            from google.genai import types
        except ImportError:
            return TranscriptionResult(
                None,
                None,
                False,
                None,
                "error",
                "google_dependency_missing",
                "google",
                False,
            )
        except ValueError as exc:
            return TranscriptionResult(None, None, False, None, "error", str(exc), "google", False)

        prompt = (
            "Transcribe this short audio. Return strict JSON with keys transcript, "
            "speech_detected, confidence, and transcription_status. Do not infer "
            "emotion, intent, identity, or provide advice."
        )
        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=audio, mime_type="audio/wav"),
                ],
            )
            return _normalize(_json_object(response.text), "google")
        except Exception:
            return TranscriptionResult(
                None,
                None,
                False,
                None,
                "error",
                "transcription_provider_error",
                "google",
                True,
            )


def create_transcriber(name: str) -> Transcriber:
    normalized = str(name or "disabled").strip().lower()
    if normalized in {"disabled", "none"}:
        return DisabledTranscriber()
    if normalized in {"google", "gemini"}:
        return GoogleTranscriber()
    raise ValueError(f"unsupported transcription provider: {normalized}")
