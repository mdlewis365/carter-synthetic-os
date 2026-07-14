# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Bounded, structured context assembly."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .contracts import NormalizedRequest, normalize_request

_DEFAULT_SYSTEM_INSTRUCTION = (
    "Act as a governed compound AI expert-system component. Distinguish "
    "known facts, model-generated content, and deterministic results."
)


@dataclass(frozen=True, slots=True)
class ContextBlock:
    name: str
    content: str
    source: str = "caller"
    priority: int = 100

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.content.strip():
            raise ValueError("context block name and content must not be empty")
        if self.priority < 0:
            raise ValueError("context block priority must not be negative")


@dataclass(frozen=True, slots=True)
class ContextAssembly:
    request: NormalizedRequest
    system_instruction: str
    anchors: tuple[str, ...]
    blocks: tuple[ContextBlock, ...]
    truncated: bool = False

    def render(self, *, include_request: bool = True) -> str:
        sections = [self.system_instruction]
        if self.anchors:
            sections.append("\n".join(self.anchors))
        sections.extend(f"[{block.name}]\n{block.content}" for block in self.blocks)
        if include_request:
            sections.append(f"[user_request]\n{self.request.text}")
        return "\n\n".join(sections)


def _coerce_block(value: ContextBlock | str | Mapping[str, Any], index: int) -> ContextBlock:
    if isinstance(value, ContextBlock):
        return value
    if isinstance(value, str):
        return ContextBlock(name=f"context_{index}", content=value)
    if isinstance(value, Mapping):
        return ContextBlock(
            name=str(value.get("name") or f"context_{index}"),
            content=str(value.get("content") or ""),
            source=str(value.get("source") or "caller"),
            priority=int(value.get("priority", 100)),
        )
    raise TypeError("context blocks must be ContextBlock, string, or mapping values")


def assemble_context(
    request: str | Mapping[str, Any] | NormalizedRequest,
    *,
    blocks: Iterable[ContextBlock | str | Mapping[str, Any]] = (),
    anchors: Iterable[Any] = (),
    system_instruction: str = _DEFAULT_SYSTEM_INSTRUCTION,
    max_chars: int = 24_000,
) -> ContextAssembly:
    """Assemble deterministic, priority-ordered context within a hard bound.

    Lower priority numbers are retained first. Context is truncated by whole
    blocks, avoiding ambiguous partial records.
    """

    normalized = normalize_request(request)
    if max_chars < len(normalized.text) + 256:
        raise ValueError("max_chars is too small for the request and instructions")
    instruction = str(system_instruction).strip()
    if not instruction:
        raise ValueError("system_instruction must not be empty")
    rendered_anchors = tuple(
        anchor.render() if hasattr(anchor, "render") else str(anchor).strip()
        for anchor in anchors
        if str(anchor).strip()
    )
    ordered = sorted(
        (_coerce_block(value, index) for index, value in enumerate(blocks)),
        key=lambda block: (block.priority, block.name, block.source),
    )

    base_size = len(instruction) + len(normalized.text) + sum(map(len, rendered_anchors)) + 64
    selected: list[ContextBlock] = []
    used = base_size
    truncated = False
    for block in ordered:
        block_size = len(block.name) + len(block.content) + len(block.source) + 16
        if used + block_size > max_chars:
            truncated = True
            continue
        selected.append(block)
        used += block_size
    return ContextAssembly(
        request=normalized,
        system_instruction=instruction,
        anchors=rendered_anchors,
        blocks=tuple(selected),
        truncated=truncated,
    )
