# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Provider-neutral, governed Synthetic Ideation System workflow."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from sos.computation import mcm

from .candidates import (
    deterministic_candidate,
    normalize_provider_candidate,
    validate_candidate,
)
from .evaluators import evaluate_candidate, govern_output
from .invention_mode_enum import normalize_mode
from .scientist_input_schema import ScientistInput

logger = logging.getLogger(__name__)

WORKFLOW_SCHEMA = "sis.workflow_result.v1"
DEFAULT_REJECTION_BOUNDARIES = [
    "Reject simple parameter tuning.",
    "Reject generic control wrappers without a distinct causal mechanism.",
    "Require an explicit causal constraint and a removal test.",
]


class IdeationWorkflow:
    """Generate, evaluate, and govern a bounded research candidate."""

    def run(
        self,
        payload: Mapping[str, Any],
        provider: Any | None = None,
    ) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            return _invalid_result("SIS payload must be a mapping.")
        try:
            mode = normalize_mode(payload.get("invention_mode") or payload.get("mode"))
        except ValueError:
            return _invalid_result("Invention mode is not supported.")

        scientist_input = _build_scientist_input(payload, mode.value)
        input_errors = scientist_input.validate()
        run_id = str(payload.get("run_id") or "").strip()[:200] or _run_id(
            scientist_input.public_payload()
        )
        backend = {
            "kind": "mock" if provider is None else "provider",
            "name": "deterministic-synthetic-candidate-generator"
            if provider is None
            else _provider_name(provider),
            "is_language_model": provider is not None,
        }

        provider_failed = False
        if input_errors:
            candidate: dict[str, Any] = {}
        elif provider is None:
            candidate = deterministic_candidate(scientist_input, mode)
        else:
            try:
                raw_candidate = _invoke_provider(
                    provider,
                    scientist_input.public_payload(),
                    mode.value,
                )
                candidate = normalize_provider_candidate(raw_candidate, scientist_input, mode)
            except Exception:
                logger.exception("SIS candidate provider failed.")
                provider_failed = True
                candidate = normalize_provider_candidate({}, scientist_input, mode)

        candidate_validation = validate_candidate(candidate)
        mcm_result = _run_feasibility_mcm(payload.get("mcm_request"))
        evaluation = (
            evaluate_candidate(candidate, mode, mcm_result)
            if candidate_validation["valid"]
            else _not_evaluated(candidate_validation["errors"])
        )
        governance = govern_output(candidate_validation["valid"], evaluation)

        errors = list(input_errors) + list(candidate_validation["errors"])
        if provider_failed:
            errors.append("Candidate provider failed.")
        status = governance["status"]
        if input_errors or provider_failed:
            status = "invalid_request" if input_errors else "provider_failure"

        return _json_safe(
            {
                "schema": WORKFLOW_SCHEMA,
                "status": status,
                "run_id": run_id,
                "fixture_id": str(payload.get("fixture_id") or "").strip()[:200] or None,
                "backend": backend,
                "scientist_input": scientist_input.public_payload(),
                "input_validation": {
                    "valid": not input_errors,
                    "errors": input_errors,
                    "warnings": [],
                },
                "candidate": candidate,
                "candidate_validation": candidate_validation,
                "mcm_feasibility": mcm_result,
                "evaluation": evaluation,
                "governance": governance,
                "errors": errors,
                "human_review_required": True,
                "execution_metadata": {
                    "workflow": "sis.governed_ideation.v1",
                    "candidate_generation_is_deterministic": provider is None,
                    "evaluation_is_deterministic": True,
                    "fixture_id": str(payload.get("fixture_id") or "").strip()[:200] or None,
                },
            }
        )


def _build_scientist_input(payload: Mapping[str, Any], mode: str) -> ScientistInput:
    framing = str(
        payload.get("framing")
        or payload.get("problem_statement")
        or payload.get("prompt")
        or payload.get("request")
        or ""
    ).strip()[:4000]
    vector = str(payload.get("exploration_vector") or framing).strip()[:2000]
    fixture_domain = (
        "synthetic inspection scheduling"
        if payload.get("fixture_id") == "synthetic_inspection_scheduler_v1"
        else "unspecified research domain"
    )
    domain = str(payload.get("domain") or fixture_domain).strip()[:300]
    boundaries = _string_list(payload.get("rejection_boundaries")) or list(
        DEFAULT_REJECTION_BOUNDARIES
    )
    return ScientistInput(
        invention_mode=mode,
        exploration_vector=vector,
        domain=domain,
        framing=framing,
        allowed_approaches=_string_list(payload.get("allowed_approaches")),
        rejection_boundaries=boundaries,
    )


def _invoke_provider(
    provider: Any,
    scientist_input: Mapping[str, Any],
    mode: str,
) -> Any:
    context = {
        "schema": "sis.provider_candidate_input.v1",
        "scientist_input": dict(scientist_input),
        "invention_mode": mode,
        "required_output_schema": "sis.concept_candidate.v1",
        "boundary": (
            "Return one research hypothesis. Do not claim novelty, patentability, "
            "feasibility, safety, or validation."
        ),
    }
    for name in ("generate_ideation_candidate", "generate_candidate", "ideate"):
        method = getattr(provider, name, None)
        if callable(method):
            return method(context)
    if callable(provider):
        return provider(context)
    raise TypeError("Provider must be callable or expose generate_ideation_candidate(context).")


def _run_feasibility_mcm(request: Any) -> dict[str, Any]:
    if request is None:
        return {
            "module": "Synthetic_OS_MCM",
            "status": "not_requested",
            "message": "No deterministic feasibility request was supplied.",
            "outputs": {},
            "diagnostics": [],
        }
    if not isinstance(request, Mapping) or not request:
        return {
            "module": "Synthetic_OS_MCM",
            "status": "needs_human_review",
            "message": "The feasibility request must be a non-empty JSON object.",
            "outputs": {},
            "diagnostics": ["Provide a valid MCM request."],
        }
    return mcm.process(deepcopy(dict(request)))


def _not_evaluated(errors: list[str]) -> dict[str, Any]:
    return {
        "rejection_boundaries": {"passed": False, "hits": []},
        "invariant_audit": {
            "passed": False,
            "score": 0.0,
            "missing_fields": [],
            "reasons": ["Candidate schema validation failed."],
        },
        "novelty_risk_score": {},
        "gate_results": [],
        "aggregate": {
            "passed": False,
            "score": 0.0,
            "blocking_gate": "candidate_schema",
            "reasons": list(errors),
            "required_actions": ["Correct the candidate schema before evaluation."],
        },
    }


def _invalid_result(message: str) -> dict[str, Any]:
    return {
        "schema": WORKFLOW_SCHEMA,
        "status": "invalid_request",
        "errors": [message],
        "human_review_required": True,
        "governance": {
            "status": "rejected",
            "candidate_is_hypothesis": True,
            "human_review_required": True,
        },
    }


def _provider_name(provider: Any) -> str:
    return str(getattr(provider, "provider_name", None) or provider.__class__.__name__)[:200]


def _run_id(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"))
    return "sis-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    items = (
        value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
        else [value]
    )
    return [str(item)[:1000] for item in items[:100] if str(item or "").strip()]


def _json_safe(value: Any, depth: int = 0) -> Any:
    if depth > 30:
        return "<maximum-depth>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if is_dataclass(value):
        return _json_safe(asdict(value), depth + 1)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item, depth + 1) for item in value]
    return str(value)
