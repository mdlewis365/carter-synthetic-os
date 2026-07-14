# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Default-deny execution boundary for explicitly registered tools."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

_TOOL_NAME = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    handler: Callable[..., Any]
    description: str = ""
    mutating: bool = False
    networked: bool = False
    requires_approval: bool = False


@dataclass(frozen=True, slots=True)
class ToolResult:
    name: str
    succeeded: bool
    value: Any = None
    error_code: str | None = None


class ToolBoundary:
    """Invoke only tools explicitly registered and allowlisted by the operator."""

    def __init__(self, *, allowlist: set[str] | frozenset[str] | tuple[str, ...] = ()) -> None:
        self._allowlist = frozenset(allowlist)
        self._tools: dict[str, ToolSpec] = {}

    @property
    def allowed_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._allowlist.intersection(self._tools)))

    def register(self, spec: ToolSpec) -> None:
        if not _TOOL_NAME.fullmatch(spec.name):
            raise ValueError("tool name must be a lowercase dotted identifier")
        if not callable(spec.handler):
            raise TypeError("tool handler must be callable")
        if spec.name in self._tools:
            raise ValueError(f"tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def invoke(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
        *,
        approved: bool = False,
    ) -> ToolResult:
        spec = self._tools.get(name)
        if spec is None:
            return ToolResult(name, False, error_code="unknown_tool")
        if name not in self._allowlist:
            return ToolResult(name, False, error_code="tool_not_allowlisted")
        if spec.requires_approval and not approved:
            return ToolResult(name, False, error_code="approval_required")
        kwargs = arguments or {}
        if not isinstance(kwargs, Mapping):
            return ToolResult(name, False, error_code="invalid_arguments")
        try:
            return ToolResult(name, True, value=spec.handler(**dict(kwargs)))
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            # Do not echo arguments or exception text; either may contain secrets.
            return ToolResult(name, False, error_code="tool_execution_failed")
