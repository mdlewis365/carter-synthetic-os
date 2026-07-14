# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Carter runtime integration across SOS providers, memory, and governance."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from hashlib import sha256
from typing import Any

from shared.config import Settings
from sos.governance import GovernanceGate, GovernanceStatus
from sos.logging import EventRecorder
from sos.memory import InMemoryAMS, RollingContextMemory
from sos.models import ModelProvider, ModelRequest, ProviderError, create_provider
from sos.orchestration import (
    ContextBlock,
    assemble_context,
    context_anchor,
    normalize_request,
    temporal_anchor,
)
from sos.sal import normalize_json

from .identity import identity_metadata, public_system_instruction


class WorkflowProviderAdapter:
    """Convert one generic provider into EAS and SIS JSON planning boundaries."""

    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider
        self.provider_name = provider.name

    def _json(self, context: Mapping[str, Any], boundary: str) -> dict[str, Any]:
        response = self.provider.generate(
            ModelRequest(
                prompt=json.dumps(context, sort_keys=True, separators=(",", ":")),
                system_prompt=(
                    public_system_instruction() + " Return one strict JSON object only. " + boundary
                ),
                temperature=0.0,
                max_tokens=3000,
            )
        )
        adjudicated = normalize_json(response.text)
        if not adjudicated.valid or adjudicated.value is None:
            raise ProviderError(
                "Provider output failed SAL JSON validation",
                provider=response.provider,
                code="schema_validation_failed",
            )
        return dict(adjudicated.value)

    def plan_engineering(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return self._json(
            context,
            "Propose an EAS stage-one plan. Do not calculate, certify, or approve.",
        )

    def generate_ideation_candidate(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return self._json(
            context,
            "Propose one SIS research hypothesis. Do not claim novelty, safety, "
            "patentability, feasibility, or validation.",
        )


class CarterRuntime:
    """Process-local governed Carter runtime. It performs no I/O at construction."""

    def __init__(
        self,
        settings: Settings,
        *,
        provider: ModelProvider | None = None,
        crm: RollingContextMemory | None = None,
        ams: InMemoryAMS | None = None,
        events: EventRecorder | None = None,
    ) -> None:
        self.settings = settings
        provider_settings: dict[str, Any] = {
            "model": settings.default_model or None,
        }
        if settings.provider == "ollama":
            provider_settings.update(
                {
                    "base_url": settings.ollama_base_url,
                    "allow_remote": settings.allow_remote_ollama,
                }
            )
        self.provider = provider or create_provider(
            settings.provider,
            model=settings.default_model or None,
            settings=provider_settings,
        )
        self.crm = crm or RollingContextMemory(
            max_turns=20,
            ttl_seconds=settings.session_idle_ttl_seconds,
        )
        self.ams = ams or InMemoryAMS(
            capacity_per_session=500,
            ttl_seconds=settings.session_idle_ttl_seconds,
        )
        self.events = events or EventRecorder(capacity=1000)
        self.governance = GovernanceGate(max_request_chars=8000)

    @property
    def workflow_provider(self) -> WorkflowProviderAdapter | None:
        if self.provider.name == "mock":
            return None
        return WorkflowProviderAdapter(self.provider)

    def _context_blocks(self, session_id: str, prompt: str) -> list[ContextBlock]:
        blocks = [
            ContextBlock(
                name="public_identity",
                content=public_system_instruction(),
                source="first_party_policy",
                priority=0,
            )
        ]
        for index, turn in enumerate(self.crm.recent(session_id, limit=12)):
            blocks.append(
                ContextBlock(
                    name=f"crm_turn_{index + 1:04d}_{turn.role}",
                    content=turn.content,
                    source="session_crm",
                    priority=20,
                )
            )
        if self.settings.enable_memory:
            for index, record in enumerate(self.ams.recall(session_id, prompt, limit=4)):
                blocks.append(
                    ContextBlock(
                        name=f"ams_recall_{index + 1}",
                        content=record.content,
                        source="session_ams",
                        priority=30,
                    )
                )
        return blocks

    def _prepare(self, session_id: str, prompt: str) -> tuple[Any, Any, Any, tuple[str, ...]]:
        normalized = normalize_request({"text": prompt, "session_id": session_id})
        gate = self.governance.evaluate_request(normalized.text)
        event = self.events.record(
            "carter.request.adjudicated",
            request_id=normalized.request_id,
            session_id=session_id,
            status=gate.status.value,
            metadata={
                "input_hash": normalized.input_hash,
                "provider": self.provider.name,
            },
        )
        anchors = (
            temporal_anchor(timezone_name="UTC"),
            context_anchor(
                session_id,
                turn_index=len(self.crm.recent(session_id)),
                labels=("public_release",),
            ),
        )
        context = assemble_context(
            normalized,
            blocks=self._context_blocks(session_id, normalized.text),
            anchors=anchors,
            system_instruction=public_system_instruction(),
            max_chars=24000,
        )
        return normalized, gate, context, (event.event_id,)

    def respond(self, session_id: str, prompt: str) -> dict[str, Any]:
        normalized, gate, context, event_ids = self._prepare(session_id, prompt)
        if gate.status is GovernanceStatus.BLOCK:
            return self._blocked_result(normalized, gate, context, event_ids)
        try:
            response = self.provider.generate(
                ModelRequest(
                    prompt=normalized.text,
                    system_prompt=context.render(include_request=False),
                    model=self.settings.default_model or None,
                    temperature=0.0,
                    metadata={"request_id": normalized.request_id},
                )
            )
        except ProviderError as exc:
            self.events.record(
                "carter.provider.failed",
                request_id=normalized.request_id,
                session_id=session_id,
                status=exc.code,
                metadata={"provider": exc.provider, "retryable": exc.retryable},
            )
            raise
        self._record_turns(session_id, normalized.text, response.text)
        completed = self.events.record(
            "carter.provider.completed",
            request_id=normalized.request_id,
            session_id=session_id,
            status="completed",
            metadata={
                "provider": response.provider,
                "model": response.model,
                "output_hash": response.output_hash,
            },
        )
        return self._result(
            normalized,
            gate,
            context,
            response.text,
            response.provider,
            response.model,
            event_ids + (completed.event_id,),
            response.metadata,
        )

    def stream(self, session_id: str, prompt: str) -> Iterator[dict[str, Any]]:
        normalized, gate, context, event_ids = self._prepare(session_id, prompt)
        yield {
            "type": "metadata",
            "request_id": normalized.request_id,
            "governance_status": gate.status.value,
            "provider": self.provider.name,
            "model": self.settings.default_model,
        }
        if gate.status is GovernanceStatus.BLOCK:
            yield {"type": "error", "error": "request_blocked_by_governance"}
            return

        chunks: list[str] = []
        try:
            request = ModelRequest(
                prompt=normalized.text,
                system_prompt=context.render(include_request=False),
                model=self.settings.default_model or None,
                temperature=0.0,
                metadata={"request_id": normalized.request_id},
            )
            for chunk in self.provider.stream(request):
                chunks.append(chunk)
                yield {"type": "token", "text": chunk}
        except ProviderError as exc:
            self.events.record(
                "carter.provider.failed",
                request_id=normalized.request_id,
                session_id=session_id,
                status=exc.code,
                metadata={"provider": exc.provider, "retryable": exc.retryable},
            )
            yield {
                "type": "error",
                "error": exc.code,
                "retryable": exc.retryable,
            }
            return

        response_text = "".join(chunks)
        self._record_turns(session_id, normalized.text, response_text)
        completed = self.events.record(
            "carter.provider.completed",
            request_id=normalized.request_id,
            session_id=session_id,
            status="completed",
            metadata={
                "provider": self.provider.name,
                "output_hash": sha256(response_text.encode("utf-8")).hexdigest(),
            },
        )
        yield {
            "type": "done",
            "event_ids": list(event_ids + (completed.event_id,)),
            "crm_turn_count": len(self.crm.recent(session_id)),
        }

    def _record_turns(self, session_id: str, prompt: str, response_text: str) -> None:
        self.crm.append(session_id, "user", prompt)
        self.crm.append(session_id, "assistant", response_text)
        if self.settings.enable_memory:
            self.ams.add(
                session_id,
                response_text,
                metadata={
                    "memory_type": "assistant_response",
                    "truth_status": "model_generated",
                },
            )

    def _result(
        self,
        normalized: Any,
        gate: Any,
        context: Any,
        response_text: str | None,
        provider: str | None,
        model: str | None,
        event_ids: tuple[str, ...],
        provider_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "schema": "carter.response.v1",
            "request": {
                "request_id": normalized.request_id,
                "session_scoped": True,
                "input_hash": normalized.input_hash,
                "normalized_text": normalized.text,
            },
            "response": response_text,
            "provider": {
                "name": provider,
                "model": model,
                "metadata": dict(provider_metadata or {}),
                "probabilistic": provider not in {None, "mock"},
            },
            "governance": {
                "status": gate.status.value,
                "reasons": list(gate.reasons),
                "requires_human_review": gate.requires_human_review,
            },
            "context": {
                "block_count": len(context.blocks),
                "truncated": context.truncated,
                "private_memory_included": False,
            },
            "memory": {
                "crm": "session_memory_only",
                "ams_enabled": self.settings.enable_memory,
                "persistent": False,
            },
            "events": list(event_ids),
            "identity": identity_metadata(),
        }

    def _blocked_result(
        self, normalized: Any, gate: Any, context: Any, event_ids: tuple[str, ...]
    ) -> dict[str, Any]:
        return self._result(normalized, gate, context, None, None, None, event_ids)

    def clear_session(self, session_id: str) -> dict[str, int]:
        return {
            "crm_turns_removed": self.crm.clear(session_id),
            "ams_records_removed": self.ams.clear(session_id),
        }
