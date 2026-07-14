# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Configurable ElevenLabs TTS boundary without bundled voices or audio."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass

MAX_TTS_CHARS = 600


@dataclass(frozen=True)
class VoiceResult:
    success: bool
    error_code: str | None
    provider: str
    audio_bytes: bytes | None = None
    content_type: str | None = None

    def public_dict(self) -> dict[str, object]:
        result = asdict(self)
        result.pop("audio_bytes", None)
        result["audio_byte_count"] = len(self.audio_bytes or b"")
        return result


class VoiceBoundary:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._speaking_sessions: set[str] = set()

    def mark_speaking(self, session_id: str, active: bool) -> None:
        with self._lock:
            if active:
                self._speaking_sessions.add(session_id)
            else:
                self._speaking_sessions.discard(session_id)

    def is_speaking(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._speaking_sessions

    def remove_session(self, session_id: str) -> None:
        with self._lock:
            self._speaking_sessions.discard(session_id)

    def status(self, session_id: str) -> dict[str, object]:
        return {
            "is_speaking": self.is_speaking(session_id),
            "provider": "elevenlabs",
            "api_key_configured": bool(os.getenv("ELEVENLABS_API_KEY")),
            "voice_id_configured": bool(os.getenv("ELEVENLABS_VOICE_ID")),
            "voice_asset_bundled": False,
            "max_text_chars": MAX_TTS_CHARS,
        }

    def synthesize(self, text: str) -> VoiceResult:
        api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
        model_id = (
            os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip()
            or "eleven_multilingual_v2"
        )
        clean_text = " ".join(str(text or "").split())
        if not api_key:
            return VoiceResult(False, "missing_elevenlabs_api_key", "elevenlabs")
        if not voice_id:
            return VoiceResult(False, "missing_elevenlabs_voice_id", "elevenlabs")
        if not clean_text:
            return VoiceResult(False, "empty_text", "elevenlabs")
        if len(clean_text) > MAX_TTS_CHARS:
            return VoiceResult(False, "text_too_long", "elevenlabs")

        encoded_voice = urllib.parse.quote(voice_id, safe="")
        url = (
            "https://api.elevenlabs.io/v1/text-to-speech/"
            + encoded_voice
            + "/stream?output_format=mp3_44100_128"
        )
        payload = json.dumps(
            {
                "text": clean_text,
                "model_id": model_id,
            }
        ).encode("utf-8")
        # The scheme and host are fixed here; only the quoted path component varies.
        request = urllib.request.Request(  # noqa: S310  # nosec B310
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", "xi-api-key": api_key},
        )
        try:
            with urllib.request.urlopen(  # noqa: S310  # nosec B310
                request, timeout=30
            ) as response:
                audio = response.read(8 * 1024 * 1024 + 1)
            if not audio or len(audio) > 8 * 1024 * 1024:
                return VoiceResult(False, "invalid_audio_response", "elevenlabs")
            return VoiceResult(True, None, "elevenlabs", audio, "audio/mpeg")
        except (urllib.error.URLError, TimeoutError, OSError):
            return VoiceResult(False, "tts_provider_error", "elevenlabs")
