# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Public, provider-neutral EAS two-stage workflow."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from sos.computation import mcm

from .decision_record import (
    build_engineering_decision_record,
    validate_engineering_decision_record,
)
from .governance import evaluate_governance
from .packs import DEFAULT_PACK_ROOT, EngineeringPack, load_pack_text, select_packs
from .schemas import (
    build_deterministic_plan,
    coerce_provider_plan,
    normalize_request,
    validate_stage_one_plan,
)

logger = logging.getLogger(__name__)

WORKFLOW_SCHEMA = "eas.workflow_result.v1"
MAX_PROVIDER_PACK_CONTEXT_CHARS = 24_000
PUBLIC_REVIEW_REASON = (
    "Carter EAS is decision-support software; a qualified human must independently "
    "verify calculations, units, assumptions, constraints, codes, and safety."
)


class EngineeringWorkflow:
    """Execute structured planning, deterministic computation, and governance."""

    def __init__(self, pack_root: Path | str | None = None) -> None:
        self.pack_root = Path(pack_root or DEFAULT_PACK_ROOT)

    def run(
        self,
        payload: Mapping[str, Any],
        provider: Any | None = None,
    ) -> dict[str, Any]:
        """Run EAS and return a JSON-safe result.

        A provider, when present, may propose only the structured stage-one plan.
        MCM execution, governance, and the mandatory human-review boundary remain
        deterministic first-party operations.
        """

        try:
            request = normalize_request(payload)
        except TypeError:
            return _json_safe(
                {
                    "schema": WORKFLOW_SCHEMA,
                    "status": "invalid_request",
                    "errors": ["EAS payload must be a mapping."],
                    "human_review_required": True,
                    "advisory": _invalid_advisory(),
                }
            )
        except ValueError:
            return _json_safe(
                {
                    "schema": WORKFLOW_SCHEMA,
                    "status": "invalid_request",
                    "errors": ["Engineering mode is not supported."],
                    "human_review_required": True,
                    "advisory": _invalid_advisory(),
                }
            )

        packs = select_packs(
            request["mode"],
            request["problem_statement"],
            request["domain"],
            pack_root=self.pack_root,
        )
        pack_dicts = [pack.public_dict() for pack in packs]
        pack_ids = [pack.pack_id for pack in packs]

        provider_failed = False
        if provider is None:
            plan = build_deterministic_plan(request, pack_ids)
            backend = plan["planning_backend"]
        else:
            backend_name = _provider_name(provider)
            try:
                raw_plan = _invoke_provider(provider, request, packs, self.pack_root)
                plan = coerce_provider_plan(raw_plan, request, pack_ids, backend_name)
            except Exception:  # Provider failures are an explicit boundary.
                logger.exception("EAS planning provider failed.")
                provider_failed = True
                plan = coerce_provider_plan({}, request, pack_ids, backend_name)
            backend = plan["planning_backend"]

        validation = validate_stage_one_plan(plan)
        case_id = request.get("case_id") or _case_id(request)
        mcm_result = _run_mcm(plan, validation.valid)
        mcm_health = mcm_result.get("mcm_run_health") or mcm.summarize_run_health(
            mcm_result,
            mcm_required=bool(plan.get("mcm_required")),
        )

        preliminary_record = build_engineering_decision_record(
            case_id=case_id,
            problem_statement=request["problem_statement"],
            engineering_mode=request["mode"],
            help_type=request["mode"],
            model_id=backend["name"],
            activation_1_json=plan,
            mcm_request=plan.get("mcm_request"),
            mcm_result=mcm_result,
            mcm_run_health=mcm_health,
            uploaded_files=[{"filename": name} for name in request["uploaded_file_names"]],
            timestamp_utc=_record_timestamp(request, provider),
        )
        gate = evaluate_governance(
            {
                **preliminary_record,
                "problem_statement": request["problem_statement"],
                "engineering_mode": request["mode"],
                "activation_1_json": plan,
                "mcm_result": mcm_result,
                "mcm_run_health": mcm_health,
            }
        )
        governance = _enforce_public_review_gate(gate)
        advisory = _build_advisory(plan, validation.valid, mcm_result, governance)
        record = build_engineering_decision_record(
            case_id=case_id,
            problem_statement=request["problem_statement"],
            engineering_mode=request["mode"],
            help_type=request["mode"],
            model_id=backend["name"],
            activation_1_json=plan,
            mcm_request=plan.get("mcm_request"),
            mcm_result=mcm_result,
            mcm_run_health=mcm_health,
            governance_result=governance,
            final_report_text=advisory["summary"],
            uploaded_files=[{"filename": name} for name in request["uploaded_file_names"]],
            timestamp_utc=_record_timestamp(request, provider),
        )
        record_validation = validate_engineering_decision_record(record)

        errors = list(validation.errors)
        if provider_failed:
            errors.append("Planning provider failed.")
        if not record_validation["valid"]:
            errors.extend(record_validation["errors"])

        status = "advisory_ready"
        if not validation.valid or provider_failed:
            status = "needs_input"
        if mcm_result.get("status") in {"error", "unsupported", "needs_human_review"}:
            status = "needs_human_review"
        if bool(plan.get("mcm_required")) and mcm_health.get("mcm_computed_ok") is not True:
            status = "needs_human_review"

        result = {
            "schema": WORKFLOW_SCHEMA,
            "status": status,
            "case_id": case_id,
            "mode": request["mode"],
            "backend": backend,
            "normalized_request": request,
            "selected_packs": pack_dicts,
            "stage_one_plan": plan,
            "schema_validation": validation.public_dict(),
            "mcm": {
                "required": bool(plan.get("mcm_required")),
                "request": plan.get("mcm_request"),
                "result": mcm_result,
                "run_health": mcm_health,
                "unit_validation": _unit_summary(mcm_result),
                "constraint_summary": _constraint_summary(mcm_result, mcm_health),
                "sensitivity": mcm_result.get("sensitivity_analysis")
                or mcm_result.get("sensitivity")
                or {},
            },
            "governance": governance,
            "engineering_decision_record": record,
            "decision_record_validation": record_validation,
            "advisory": advisory,
            "errors": errors,
            "human_review_required": True,
            "professional_boundary": PUBLIC_REVIEW_REASON,
            "execution_metadata": {
                "workflow": "eas.two_stage.v1",
                "planning_is_deterministic": provider is None,
                "computation_is_deterministic": True,
                "fixture_id": request.get("fixture_id"),
                "record_timestamp_source": (
                    "caller"
                    if request.get("timestamp_utc")
                    else "fixed_synthetic_fixture"
                    if provider is None
                    else "runtime"
                ),
            },
        }
        result["structured_plan"] = result["stage_one_plan"]
        result["validation"] = result["schema_validation"]
        result["computation"] = result["mcm"]
        result["final_response"] = result["advisory"]
        return _json_safe(result)


def _invoke_provider(
    provider: Any,
    request: Mapping[str, Any],
    packs: list[EngineeringPack],
    pack_root: Path,
) -> Any:
    context = {
        "schema": "eas.provider_planning_input.v1",
        "request": dict(request),
        "selected_packs": _provider_pack_context(packs, pack_root),
        "required_output_schema": "eas.stage_one_plan.v1",
        "boundary": "Provider proposes a plan only; it does not compute or approve.",
    }
    for name in ("plan_engineering", "create_engineering_plan", "plan"):
        method = getattr(provider, name, None)
        if callable(method):
            return method(context)
    if callable(provider):
        return provider(context)
    raise TypeError("Provider must be callable or expose plan_engineering(context).")


def _provider_pack_context(packs: list[EngineeringPack], pack_root: Path) -> list[dict[str, Any]]:
    """Load bounded first-party guidance as inert planning context."""

    remaining = MAX_PROVIDER_PACK_CONTEXT_CHARS
    context: list[dict[str, Any]] = []
    for pack in packs:
        text = load_pack_text(pack, pack_root)
        excerpt = text[:remaining]
        context.append(
            {
                **pack.public_dict(),
                "guidance_text": excerpt,
                "guidance_truncated": len(excerpt) < len(text),
            }
        )
        remaining -= len(excerpt)
        if remaining <= 0:
            break
    return context


def _provider_name(provider: Any) -> str:
    name = getattr(provider, "provider_name", None) or provider.__class__.__name__
    return str(name)[:200]


def _run_mcm(plan: Mapping[str, Any], plan_valid: bool) -> dict[str, Any]:
    required = bool(plan.get("mcm_required"))
    request = plan.get("mcm_request")
    if not required:
        return {
            "module": "Synthetic_OS_MCM",
            "status": "not_required",
            "message": "The validated stage-one plan did not require deterministic computation.",
            "outputs": {},
            "diagnostics": [],
            "mcm_run_health": mcm.summarize_run_health(None, mcm_required=False),
        }
    if not plan_valid or not isinstance(request, Mapping):
        return {
            "module": "Synthetic_OS_MCM",
            "status": "needs_human_review",
            "message": "MCM was not run because the stage-one plan was invalid.",
            "outputs": {},
            "diagnostics": ["Correct stage-one schema errors before deterministic computation."],
            "mcm_run_health": mcm.summarize_run_health(None, mcm_required=True),
        }
    return mcm.process(deepcopy(dict(request)))


def _enforce_public_review_gate(gate: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(gate)
    source_status = str(result.get("governance_status") or "unknown")
    result["deterministic_gate_status"] = source_status
    result["deterministic_status_label"] = str(result.get("final_report_status_label") or "unknown")
    result["governance_status"] = "needs_human_review"
    result["human_review_required"] = True
    result["final_report_status_label"] = "Engineering advisory - qualified human review required"
    result["user_facing_status_label"] = result["final_report_status_label"]
    reasons = [str(item) for item in result.get("governance_reasons") or []]
    if PUBLIC_REVIEW_REASON not in reasons:
        reasons.append(PUBLIC_REVIEW_REASON)
    result["governance_reasons"] = reasons
    result["public_release_gate"] = "mandatory_human_review"
    result["professional_approval_status"] = "not_approved"
    return result


def _build_advisory(
    plan: Mapping[str, Any],
    plan_valid: bool,
    mcm_result: Mapping[str, Any],
    governance: Mapping[str, Any],
) -> dict[str, Any]:
    if not plan_valid:
        summary = "No engineering advisory was produced because the structured plan is invalid."
    elif mcm_result.get("status") == "not_required":
        summary = (
            "The deterministic planner completed without an MCM calculation. "
            "The proposed work remains an unapproved engineering advisory."
        )
    elif (
        mcm_result.get("status") == "computed"
        and isinstance(mcm_result.get("mcm_run_health"), Mapping)
        and mcm_result["mcm_run_health"].get("mcm_computed_ok") is not True
    ):
        health = mcm_result["mcm_run_health"]
        failed = _safe_count(health.get("constraint_failed"))
        unknown = _safe_count(health.get("constraint_unknown"))
        details = []
        if failed:
            details.append(f"{failed} constraint check(s) failed")
        if unknown:
            details.append(f"{unknown} constraint check(s) remain unknown")
        detail_text = ("; " + "; ".join(details) + ".") if details else "."
        summary = (
            "MCM completed deterministic computation, but run health requires human review"
            + detail_text
            + " Do not use the result until all blocking diagnostics are resolved."
        )
    elif mcm_result.get("status") == "computed":
        output_names = ", ".join(sorted(str(key) for key in (mcm_result.get("outputs") or {})))
        summary = (
            "MCM completed deterministic computation"
            + (f" for: {output_names}." if output_names else ".")
            + " Results are not a professional certification or approval."
        )
    else:
        summary = (
            f"MCM status is {mcm_result.get('status') or 'unknown'}; "
            "do not use this result for an engineering decision without resolving diagnostics."
        )
    return {
        "kind": "deterministic_engineering_advisory",
        "summary": summary,
        "computed_outputs": dict(mcm_result.get("outputs") or {}),
        "deterministic_gate_status": governance.get("deterministic_gate_status"),
        "recommended_actions": [
            "Review the structured assumptions and required inputs.",
            "Independently reproduce calculations and unit conversions.",
            "Check applicable codes, standards, hazards, and acceptance criteria.",
            "Obtain approval from an appropriately qualified professional.",
        ],
        "human_review_required": True,
        "limitations": [
            "EAS does not replace licensed engineering judgment.",
            "EAS does not establish code compliance or safety.",
            "A computed result does not establish experimental or production validation.",
        ],
    }


def _invalid_advisory() -> dict[str, Any]:
    return {
        "kind": "deterministic_engineering_advisory",
        "summary": "No advisory was produced because the request is invalid.",
        "computed_outputs": {},
        "recommended_actions": ["Provide a supported mode and a problem statement."],
        "human_review_required": True,
        "limitations": ["EAS does not replace licensed engineering judgment."],
    }


def _safe_count(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    return max(0, result)


def _unit_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    checks = result.get("unit_validation")
    return {
        "checks": checks if isinstance(checks, (list, dict)) else [],
        "warnings": list(result.get("unit_warnings") or []),
        "invalid_outputs": list(result.get("invalid_unit_outputs") or []),
    }


def _constraint_summary(
    result: Mapping[str, Any],
    health: Mapping[str, Any],
) -> dict[str, Any]:
    checks = result.get("constraint_checks")
    if isinstance(checks, Mapping) and isinstance(checks.get("summary"), Mapping):
        return dict(checks["summary"])
    summary = result.get("constraint_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    return {
        "total": int(health.get("constraint_total") or 0),
        "passed": int(health.get("constraint_passed") or 0),
        "failed": int(health.get("constraint_failed") or 0),
        "unknown": int(health.get("constraint_unknown") or 0),
    }


def _record_timestamp(request: Mapping[str, Any], provider: Any | None) -> Any:
    if request.get("timestamp_utc"):
        return request["timestamp_utc"]
    if provider is None:
        return "2000-01-01T00:00:00+00:00"
    return None


def _case_id(request: Mapping[str, Any]) -> str:
    canonical = json.dumps(_json_safe(dict(request)), sort_keys=True, separators=(",", ":"))
    return "eas-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


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
