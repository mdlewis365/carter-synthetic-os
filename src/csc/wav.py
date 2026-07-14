# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Strict in-memory WAV validation and deterministic PCM16 encoding."""

from __future__ import annotations

import math
import wave
from array import array
from dataclasses import asdict, dataclass
from io import BytesIO

MAX_AUDIO_BYTES = 4 * 1024 * 1024
MAX_AUDIO_SECONDS = 30.0


@dataclass(frozen=True)
class WavMetadata:
    channels: int
    sample_width_bytes: int
    sample_rate_hz: int
    frame_count: int
    duration_seconds: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_wav(data: bytes) -> WavMetadata:
    if not data:
        raise ValueError("empty_audio")
    if len(data) > MAX_AUDIO_BYTES:
        raise ValueError("audio_too_large")
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("invalid_wav_header")
    try:
        with wave.open(BytesIO(data), "rb") as wav_file:
            metadata = WavMetadata(
                channels=wav_file.getnchannels(),
                sample_width_bytes=wav_file.getsampwidth(),
                sample_rate_hz=wav_file.getframerate(),
                frame_count=wav_file.getnframes(),
                duration_seconds=(
                    wav_file.getnframes() / wav_file.getframerate()
                    if wav_file.getframerate()
                    else 0.0
                ),
            )
    except (EOFError, wave.Error) as exc:
        raise ValueError("invalid_wav") from exc
    if metadata.channels not in {1, 2}:
        raise ValueError("unsupported_channel_count")
    if metadata.sample_width_bytes != 2:
        raise ValueError("pcm16_required")
    if not 8000 <= metadata.sample_rate_hz <= 96000:
        raise ValueError("unsupported_sample_rate")
    if metadata.duration_seconds > MAX_AUDIO_SECONDS:
        raise ValueError("audio_too_long")
    return metadata


def encode_pcm16(
    samples: list[float] | tuple[float, ...],
    *,
    sample_rate_hz: int,
    channels: int = 1,
) -> bytes:
    """Encode normalized floating-point samples as a reproducible WAV buffer."""

    if channels not in {1, 2}:
        raise ValueError("channels must be 1 or 2")
    if not 8000 <= sample_rate_hz <= 96000:
        raise ValueError("sample_rate_hz out of range")
    pcm = array("h")
    for sample in samples:
        value = 0.0 if not math.isfinite(float(sample)) else float(sample)
        value = max(-1.0, min(1.0, value))
        pcm.append(int(round(value * (32767 if value >= 0 else 32768))))
    output = BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate_hz)
        wav_file.writeframes(pcm.tobytes())
    return output.getvalue()
