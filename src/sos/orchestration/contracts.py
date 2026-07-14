# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Data contracts shared by SOS orchestration stages."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sos.governance import GateDecision
    from sos.models import ModelResponse

    from .context import ContextAssembly

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MAX_REQUEST_CHARS = 100_000


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_datetime(value: Any) -> datetime:
    if value is None:
        return _utc_now()
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("created_at must be an ISO-8601 timestamp") from exc
    else:
        raise TypeError("created_at must be a datetime or ISO-8601 string")
    if parsed.tzinfo is None:
        raise ValueError("created_at must include a timezone")
    return parsed.astimezone(UTC)


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("request text must be a string")
    cleaned = _CONTROL_CHARACTERS.sub("", value).strip()
    if not cleaned:
        raise ValueError("request text must not be empty")
    if len(cleaned) > _MAX_REQUEST_CHARS:
        raise ValueError(f"request text exceeds {_MAX_REQUEST_CHARS} characters")
    return cleaned


@dataclass(frozen=True, slots=True)
class NormalizedRequest:
    """A validated request entering a governed SOS pipeline."""

    request_id: str
    session_id: str
    text: str
    created_at: datetime
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id or not self.session_id:
            raise ValueError("request_id and session_id must not be empty")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    @property
    def input_hash(self) -> str:
        return sha256(self.text.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Auditable output from one request pipeline execution."""

    request: NormalizedRequest
    context: ContextAssembly
    governance: GateDecision
    response: ModelResponse | None
    event_ids: tuple[str, ...] = ()


def normalize_request(
    value: str | Mapping[str, Any] | NormalizedRequest,
    *,
    session_id: str | None = None,
) -> NormalizedRequest:
    """Normalize text or a request mapping without retaining the raw mapping.

    A caller can supply ``request_id`` and ``created_at`` for reproducible runs.
    Otherwise the request identifier is derived from the session and content;
    this intentionally contains no raw prompt text.
    """

    if isinstance(value, NormalizedRequest):
        if session_id is not None and session_id != value.session_id:
            raise ValueError("session_id does not match the normalized request")
        return value

    if isinstance(value, str):
        payload: Mapping[str, Any] = {"text": value}
    elif isinstance(value, Mapping):
        payload = value
    else:
        raise TypeError("request must be text, a mapping, or NormalizedRequest")

    text = _clean_text(payload.get("text", payload.get("input")))
    resolved_session = str(session_id or payload.get("session_id") or "public-demo").strip()
    if not resolved_session or len(resolved_session) > 200:
        raise ValueError("session_id must contain between 1 and 200 characters")
    request_id = str(payload.get("request_id") or "").strip()
    if not request_id:
        request_id = sha256(f"{resolved_session}\x00{text}".encode()).hexdigest()[:24]
    if len(request_id) > 200:
        raise ValueError("request_id must not exceed 200 characters")
    attributes = payload.get("attributes") or {}
    if not isinstance(attributes, Mapping):
        raise TypeError("attributes must be a mapping")

    return NormalizedRequest(
        request_id=request_id,
        session_id=resolved_session,
        text=text,
        created_at=_parse_datetime(payload.get("created_at")),
        attributes=attributes,
    )
