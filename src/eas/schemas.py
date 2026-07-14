# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Structured stage-one planning schema and validation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from .fixtures import fixture_mcm_request
from .modes import normalize_mode

PLAN_SCHEMA = "eas.stage_one_plan.v1"
MAX_PROBLEM_CHARS = 8000
_SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "client_secret",
    "cookie",
    "credential",
    "credentials",
    "password",
    "refresh_token",
    "secret",
    "secret_key",
    "session_cookie",
    "token",
    "access_token",
}


@dataclass(frozen=True)
class PlanValidation:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Retain only public workflow fields; uploaded content is never retained."""

    if not isinstance(payload, Mapping):
        raise TypeError("EAS payload must be a mapping.")
    mode = normalize_mode(
        payload.get("mode") or payload.get("engineering_mode") or payload.get("help_type")
    )
    statement = str(
        payload.get("problem_statement") or payload.get("problem") or payload.get("request") or ""
    ).strip()
    files = payload.get("uploaded_files") or payload.get("files") or []
    file_names: list[str] = []
    if isinstance(files, Sequence) and not isinstance(files, (str, bytes, bytearray)):
        for item in files:
            if isinstance(item, Mapping):
                name = item.get("filename") or item.get("name")
            else:
                name = getattr(item, "filename", None) or getattr(item, "name", None)
            if name:
                file_names.append(str(name).replace("\\", "/").rsplit("/", 1)[-1][:255])

    return {
        "mode": mode.value,
        "problem_statement": statement[:MAX_PROBLEM_CHARS],
        "domain": str(payload.get("domain") or "").strip()[:200],
        "objective": str(payload.get("objective") or statement).strip()[:1000],
        "assumptions": _string_list(payload.get("assumptions")),
        "required_inputs": _string_list(payload.get("required_inputs")),
        "uploaded_file_names": file_names,
        "mcm_required": _optional_bool(payload.get("mcm_required")),
        "mcm_request": _mapping_or_none(payload.get("mcm_request") or payload.get("computation")),
        "operation": str(payload.get("operation") or "").strip()[:100] or None,
        "expression": str(payload.get("expression") or "").strip()[:4000] or None,
        "inputs": _mapping_or_none(payload.get("inputs")),
        "variables": _mapping_or_none(payload.get("variables")),
        "constants": _mapping_or_none(payload.get("constants")),
        "equations": _structured_list(payload.get("equations")),
        "constraints": _structured_list(payload.get("constraints")),
        "solve_for": _string_list(payload.get("solve_for")),
        "requested_output": _sanitize_value(payload.get("requested_output")),
        "sensitivity": _mapping_or_none(
            payload.get("sensitivity") or payload.get("sensitivity_analysis")
        ),
        "timestamp_utc": payload.get("timestamp_utc"),
        "case_id": str(payload.get("case_id") or "").strip()[:200] or None,
        "fixture_id": str(payload.get("fixture_id") or "").strip()[:200] or None,
    }


def build_deterministic_plan(
    request: Mapping[str, Any],
    selected_pack_ids: Sequence[str],
) -> dict[str, Any]:
    """Build a transparent rule-based plan; this is not language-model output."""

    mcm_request = (
        _mapping_or_none(request.get("mcm_request"))
        or fixture_mcm_request(request.get("fixture_id"))
        or _construct_mcm_request(request)
    )
    required_flag = request.get("mcm_required")
    mcm_required = bool(mcm_request) if required_flag is None else bool(required_flag)
    equations = []
    constraints = []
    if mcm_request:
        raw_equations = mcm_request.get("equations")
        if isinstance(raw_equations, list):
            equations = raw_equations
        raw_constraints = mcm_request.get("constraints")
        if isinstance(raw_constraints, list):
            constraints = raw_constraints

    return {
        "schema": PLAN_SCHEMA,
        "mode": str(request["mode"]),
        "problem_statement": str(request.get("problem_statement") or ""),
        "objective": str(request.get("objective") or ""),
        "assumptions": list(request.get("assumptions") or []),
        "required_inputs": list(request.get("required_inputs") or []),
        "equations": equations,
        "constraints": constraints,
        "mcm_required": mcm_required,
        "mcm_request": mcm_request,
        "selected_packs": list(selected_pack_ids),
        "planning_backend": {
            "kind": "mock",
            "name": "deterministic-synthetic-planner",
            "is_language_model": False,
        },
        "human_review_required": True,
        "synthetic_fixture": (
            request.get("fixture_id") if mcm_request and request.get("fixture_id") else None
        ),
    }


def coerce_provider_plan(
    raw_plan: Any,
    request: Mapping[str, Any],
    selected_pack_ids: Sequence[str],
    backend_name: str,
) -> dict[str, Any]:
    """Normalize provider output before schema validation."""

    source = dict(raw_plan) if isinstance(raw_plan, Mapping) else {}
    allowed_fields = (
        "schema",
        "mode",
        "problem_statement",
        "objective",
        "assumptions",
        "required_inputs",
        "equations",
        "constraints",
        "mcm_required",
        "mcm_request",
    )
    plan = {name: source.get(name) for name in allowed_fields}
    plan["schema"] = str(plan.get("schema") or PLAN_SCHEMA)
    try:
        plan["mode"] = normalize_mode(plan.get("mode") or request["mode"]).value
    except ValueError:
        plan["mode"] = str(plan.get("mode") or "")
    plan["problem_statement"] = str(
        plan.get("problem_statement") or request.get("problem_statement") or ""
    )[:MAX_PROBLEM_CHARS]
    plan["objective"] = str(plan.get("objective") or request.get("objective") or "")[:1000]
    for field_name in ("assumptions", "required_inputs"):
        plan[field_name] = _string_list(plan.get(field_name))
    for field_name in ("equations", "constraints"):
        plan[field_name] = _structured_list(plan.get(field_name))
    plan["mcm_request"] = _mapping_or_none(plan.get("mcm_request"))
    parsed_mcm_required = _optional_bool(plan.get("mcm_required"))
    plan["mcm_required"] = (
        bool(plan["mcm_request"]) if parsed_mcm_required is None else bool(parsed_mcm_required)
    )
    plan["selected_packs"] = list(selected_pack_ids)
    plan["planning_backend"] = {
        "kind": "provider",
        "name": backend_name,
        "is_language_model": True,
    }
    plan["human_review_required"] = True
    return plan


def validate_stage_one_plan(plan: Any) -> PlanValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, Mapping):
        return PlanValidation(False, ["plan must be a JSON object"], [])

    if plan.get("schema") != PLAN_SCHEMA:
        errors.append(f"schema must equal {PLAN_SCHEMA}")
    try:
        normalize_mode(plan.get("mode"))
    except ValueError:
        errors.append("mode is not supported")
    if not str(plan.get("problem_statement") or "").strip():
        errors.append("problem_statement is required")
    list_fields = ("assumptions", "required_inputs", "equations", "constraints", "selected_packs")
    for field_name in list_fields:
        if not isinstance(plan.get(field_name), list):
            errors.append(f"{field_name} must be a list")
    if plan.get("human_review_required") is not True:
        errors.append("human_review_required must be true")
    if not isinstance(plan.get("planning_backend"), Mapping):
        errors.append("planning_backend must be an object")

    if bool(plan.get("mcm_required")):
        request = plan.get("mcm_request")
        if not isinstance(request, Mapping) or not request:
            errors.append("mcm_request is required when mcm_required is true")
    elif plan.get("mcm_request"):
        warnings.append("mcm_request was supplied while mcm_required is false")

    for index, equation in enumerate(plan.get("equations") or []):
        if not isinstance(equation, (str, Mapping)):
            errors.append(f"equations[{index}] must be a string or object")
    return PlanValidation(not errors, errors, warnings)


def _mapping_or_none(value: Any) -> dict[str, Any] | None:
    return _sanitize_mapping(value) if isinstance(value, Mapping) else None


def _sanitize_mapping(value: Mapping[Any, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for raw_key, item in value.items():
        key = str(raw_key)
        normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
        if _is_sensitive_key(normalized):
            continue
        if isinstance(item, Mapping):
            sanitized[key] = _sanitize_mapping(item)
        elif isinstance(item, (list, tuple)):
            sanitized[key] = [_sanitize_value(entry) for entry in item]
        else:
            sanitized[key] = item
    return sanitized


def _is_sensitive_key(normalized: str) -> bool:
    if normalized in _SENSITIVE_KEYS:
        return True
    suffixes = ("api_key", "password", "secret", "token", "cookie", "credential")
    return any(normalized.endswith(f"_{suffix}") for suffix in suffixes)


def _construct_mcm_request(request: Mapping[str, Any]) -> dict[str, Any] | None:
    if not (request.get("operation") or request.get("expression") or request.get("equations")):
        return None
    result: dict[str, Any] = {
        "mode": request.get("mode"),
        "objective": request.get("objective"),
    }
    for field_name in (
        "operation",
        "expression",
        "inputs",
        "variables",
        "constants",
        "equations",
        "constraints",
        "solve_for",
        "requested_output",
        "sensitivity",
    ):
        value = request.get(field_name)
        if value not in (None, [], {}):
            result[field_name] = _sanitize_value(value)
    return result


def _structured_list(value: Any) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [_sanitize_value(item) for item in value[:200]]


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(item) for item in value]
    return value


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    items = (
        value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
        else [value]
    )
    result = []
    for item in items[:100]:
        text = str(item or "").strip()
        if text:
            result.append(text[:1000])
    return result


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
