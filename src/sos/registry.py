# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Declarative registry for public SOS components and their boundaries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ComponentDescriptor:
    name: str
    category: str
    import_path: str
    deterministic: bool
    persistence: str = "none"
    network: str = "none"
    status: str = "implemented"


class SubsystemRegistry:
    """Registry of descriptors only; lookup never imports or initializes code."""

    def __init__(self, descriptors: Iterable[ComponentDescriptor] = ()) -> None:
        self._items: dict[str, ComponentDescriptor] = {}
        for descriptor in descriptors:
            self.register(descriptor)

    def register(self, descriptor: ComponentDescriptor) -> None:
        if not descriptor.name.strip() or not descriptor.import_path.strip():
            raise ValueError("component name and import_path must not be empty")
        if descriptor.name in self._items:
            raise ValueError(f"component already registered: {descriptor.name}")
        self._items[descriptor.name] = descriptor

    def get(self, name: str) -> ComponentDescriptor:
        try:
            return self._items[name]
        except KeyError as exc:
            raise KeyError(f"unknown SOS component: {name}") from exc

    def list(self, *, category: str | None = None) -> tuple[ComponentDescriptor, ...]:
        items = self._items.values()
        if category is not None:
            items = (item for item in items if item.category == category)
        return tuple(sorted(items, key=lambda item: item.name))


def default_registry() -> SubsystemRegistry:
    """Return declared 0.1.0 public components without instantiating them."""

    return SubsystemRegistry(
        (
            ComponentDescriptor("orchestration", "core", "sos.orchestration:run_pipeline", True),
            ComponentDescriptor("governance", "core", "sos.governance:GovernanceGate", True),
            ComponentDescriptor("sal", "core", "sos.sal:normalize_json", True),
            ComponentDescriptor("ams.in_memory", "memory", "sos.memory:InMemoryAMS", True),
            ComponentDescriptor("crm", "memory", "sos.memory:RollingContextMemory", True),
            ComponentDescriptor("dim", "memory", "sos.memory:DIMIngestor", True),
            ComponentDescriptor(
                "ams.sqlite", "memory", "sos.memory:SQLiteMemoryStore", True, "opt-in"
            ),
            ComponentDescriptor(
                "ams.chroma",
                "memory",
                "sos.memory:ChromaMemoryStore",
                False,
                "opt-in",
                "embedding-provider-dependent",
            ),
            ComponentDescriptor("provider.mock", "model", "sos.models:create_provider", True),
            ComponentDescriptor(
                "provider.ollama", "model", "sos.models:create_provider", False, "none", "loopback"
            ),
            ComponentDescriptor(
                "provider.cloud", "model", "sos.models:create_provider", False, "provider", "opt-in"
            ),
            ComponentDescriptor("lcm", "observability", "sos.logging:LifecycleMonitor", True),
            ComponentDescriptor("tool_boundary", "governance", "sos.governance:ToolBoundary", True),
        )
    )
