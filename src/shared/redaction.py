# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Small defensive redaction helpers for logs and public metadata."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEY = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|credential|cookie|authorization|private)"
)
BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
URL_CREDENTIAL = re.compile(r"(?i)(https?://)([^/@\s:]+):([^/@\s]+)@")


def redact_text(value: object, *, limit: int = 1000) -> str:
    text = str(value or "")
    text = BEARER.sub("Bearer [REDACTED]", text)
    text = URL_CREDENTIAL.sub(r"\1[REDACTED]@", text)
    return text[:limit]


def redact_mapping(
    value: Mapping[str, Any] | None,
    *,
    depth: int = 0,
    max_depth: int = 5,
) -> dict[str, Any]:
    if not value or depth >= max_depth:
        return {}
    result: dict[str, Any] = {}
    for raw_key, item in value.items():
        key = str(raw_key)
        if SENSITIVE_KEY.search(key):
            result[key] = "[REDACTED]"
        elif isinstance(item, Mapping):
            result[key] = redact_mapping(item, depth=depth + 1, max_depth=max_depth)
        elif isinstance(item, (list, tuple)):
            result[key] = [
                redact_mapping(entry, depth=depth + 1, max_depth=max_depth)
                if isinstance(entry, Mapping)
                else redact_text(entry)
                if isinstance(entry, str)
                else entry
                for entry in item[:50]
            ]
        elif isinstance(item, str):
            result[key] = redact_text(item)
        elif item is None or isinstance(item, (bool, int, float)):
            result[key] = item
        else:
            result[key] = redact_text(item)
    return result
