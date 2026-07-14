# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Session-isolated sensory state with bounded, in-memory transcript retention."""

from __future__ import annotations

import math
import re
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

WAKE_NAME = re.compile(r"\bcarter\b", re.IGNORECASE)
ATTENTION_CLASSES = {"focused", "peripheral", "ignored", "background"}


def classify_attention(
    transcript: str | None,
    *,
    speech_detected: bool | None,
    carter_is_speaking: bool = False,
) -> str:
    """Apply the deterministic low-authority attention classification."""

    if carter_is_speaking:
        return "ignored"
    text = str(transcript or "").strip()
    if speech_detected is False or not text:
        return "background"
    if WAKE_NAME.search(text):
        return "focused"
    return "peripheral"


@dataclass(frozen=True)
class TranscriptEvent:
    sequence: int
    timestamp_utc: str
    transcript: str
    speech_detected: bool | None
    wake_name_detected: bool
    attention: str
    confidence: float | None
    source: str = "browser_microphone"

    def public_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class _SessionState:
    hearing_active: bool = False
    camera_active: bool = False
    started_at: str | None = None
    last_changed_at: str | None = None
    next_sequence: int = 1
    events: deque[tuple[float, TranscriptEvent]] = field(default_factory=deque)
    latest_interpretation: dict[str, object] | None = None


class SensorySessionStore:
    """Thread-safe state keyed only by the current signed web session."""

    def __init__(
        self,
        *,
        window_seconds: int = 60,
        max_events: int = 24,
        session_ttl_seconds: int = 3600,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if window_seconds <= 0 or max_events <= 0 or session_ttl_seconds <= 0:
            raise ValueError("window_seconds, max_events, and session_ttl_seconds must be positive")
        self.window_seconds = min(window_seconds, 3600)
        self.max_events = min(max_events, 240)
        self.session_ttl_seconds = min(session_ttl_seconds, 86400)
        self._clock = clock
        self._lock = threading.RLock()
        self._sessions: dict[str, _SessionState] = {}
        self._last_seen: dict[str, float] = {}

    @staticmethod
    def _utc_now(epoch: float) -> str:
        return datetime.fromtimestamp(epoch, UTC).isoformat()

    @staticmethod
    def _key(session_id: str) -> str:
        key = str(session_id or "").strip()
        if not key:
            raise ValueError("session_id is required")
        return key

    def _prune_sessions_locked(self, now: float) -> None:
        cutoff = now - self.session_ttl_seconds
        for session_id, last_seen in list(self._last_seen.items()):
            if last_seen < cutoff:
                self._sessions.pop(session_id, None)
                self._last_seen.pop(session_id, None)

    def _state(self, session_id: str, now: float) -> _SessionState:
        self._prune_sessions_locked(now)
        key = self._key(session_id)
        self._last_seen[key] = now
        return self._sessions.setdefault(key, _SessionState())

    def _prune(self, state: _SessionState, now: float) -> None:
        cutoff = now - self.window_seconds
        while state.events and state.events[0][0] < cutoff:
            state.events.popleft()
        while len(state.events) > self.max_events:
            state.events.popleft()

    def set_hearing(self, session_id: str, active: bool) -> dict[str, object]:
        now = self._clock()
        with self._lock:
            state = self._state(session_id, now)
            state.hearing_active = bool(active)
            state.last_changed_at = self._utc_now(now)
            if active and not state.started_at:
                state.started_at = state.last_changed_at
            return self._snapshot_locked(state, now)

    def set_camera(self, session_id: str, active: bool) -> dict[str, object]:
        now = self._clock()
        with self._lock:
            state = self._state(session_id, now)
            state.camera_active = bool(active)
            state.last_changed_at = self._utc_now(now)
            return self._snapshot_locked(state, now)

    def add_transcript(
        self,
        session_id: str,
        transcript: str | None,
        *,
        speech_detected: bool | None = True,
        confidence: float | None = None,
        carter_is_speaking: bool = False,
        source: str = "browser_microphone",
        require_hearing: bool = True,
    ) -> TranscriptEvent:
        now = self._clock()
        clean_text = " ".join(str(transcript or "").split())[:2000]
        attention = classify_attention(
            clean_text,
            speech_detected=speech_detected,
            carter_is_speaking=carter_is_speaking,
        )
        normalized_confidence: float | None
        try:
            normalized_confidence = None if confidence is None else float(confidence)
            if normalized_confidence is not None and not math.isfinite(normalized_confidence):
                normalized_confidence = None
            elif normalized_confidence is not None:
                normalized_confidence = max(0.0, min(1.0, normalized_confidence))
        except (TypeError, ValueError):
            normalized_confidence = None

        with self._lock:
            state = self._state(session_id, now)
            if require_hearing and not state.hearing_active:
                raise PermissionError("hearing is not active for this session")
            event = TranscriptEvent(
                sequence=state.next_sequence,
                timestamp_utc=self._utc_now(now),
                transcript=clean_text,
                speech_detected=speech_detected,
                wake_name_detected=bool(WAKE_NAME.search(clean_text)),
                attention=attention,
                confidence=normalized_confidence,
                source=str(source or "unknown")[:80],
            )
            state.next_sequence += 1
            state.events.append((now, event))
            self._prune(state, now)
            return event

    def context(self, session_id: str) -> dict[str, object]:
        now = self._clock()
        with self._lock:
            state = self._state(session_id, now)
            self._prune(state, now)
            events = [event.public_dict() for _, event in state.events]
            return {
                **self._snapshot_locked(state, now),
                "events": events,
                "transcript_text": "\n".join(
                    str(event["transcript"]) for event in events if event["transcript"]
                ),
            }

    def snapshot(self, session_id: str) -> dict[str, object]:
        now = self._clock()
        with self._lock:
            state = self._state(session_id, now)
            return self._snapshot_locked(state, now)

    def _snapshot_locked(self, state: _SessionState, now: float) -> dict[str, object]:
        self._prune(state, now)
        return {
            "hearing_active": state.hearing_active,
            "camera_active": state.camera_active,
            "started_at": state.started_at,
            "last_changed_at": state.last_changed_at,
            "event_count": len(state.events),
            "window_seconds": self.window_seconds,
            "max_events": self.max_events,
            "session_idle_ttl_seconds": self.session_ttl_seconds,
            "session_scoped": True,
            "raw_audio_retained": False,
            "camera_frames_retained": False,
            "persistence": "memory_only",
            "requires_explicit_activation": True,
            "latest_interpretation": state.latest_interpretation,
        }

    def set_interpretation(self, session_id: str, interpretation: dict[str, object]) -> None:
        now = self._clock()
        with self._lock:
            self._state(session_id, now).latest_interpretation = dict(interpretation)

    def clear(self, session_id: str) -> dict[str, object]:
        now = self._clock()
        with self._lock:
            state = self._state(session_id, now)
            state.events.clear()
            state.latest_interpretation = None
            return self._snapshot_locked(state, now)

    def remove_session(self, session_id: str) -> None:
        with self._lock:
            key = self._key(session_id)
            self._sessions.pop(key, None)
            self._last_seen.pop(key, None)
