# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""
Canonical Engineering Decision Record helpers for EAS.

The record intentionally stores compact, decision-relevant summaries. It does
not store uploaded document contents or raw provider payloads.
"""

from __future__ import annotations

import datetime
import json
import math
import os
from typing import Any

UNKNOWN = "unknown"
MAX_TEXT_CHARS = 8000
MAX_SUMMARY_TEXT_CHARS = 700
MAX_LIST_ITEMS = 40


def build_engineering_decision_record(
    *,
    case_id: Any = None,
    problem_statement: Any = None,
    engineering_mode: Any = None,
    help_type: Any = None,
    model_id: Any = None,
    activation_1_json: Any = None,
    mcm_request: Any = None,
    mcm_result: Any = None,
    mcm_run_health: Any = None,
    governance_result: Any = None,
    final_report_text: Any = None,
    uploaded_files: Any = None,
    timestamp_utc: Any = None,
) -> dict:
    """
    Build a defensive Engineering Decision Record from current EAS artifacts.

    Inputs may be missing or malformed; the function normalizes unknown values
    instead of raising.
    """

    activation = _as_dict(activation_1_json)
    request_obj = _as_dict(mcm_request) or _as_dict(activation.get("mcm_request"))
    result = _as_dict(mcm_result)
    health = _as_dict(mcm_run_health)
    governance = _as_dict(governance_result)

    mcm_required = _bool_or_default(
        activation.get("mcm_required"),
        default=bool(request_obj) or bool(health.get("mcm_required")),
    )
    mcm_status = _first_non_empty(
        health.get("mcm_status"),
        result.get("status"),
        "not_required" if not mcm_required else UNKNOWN,
    )
    mcm_computed_ok = _bool_or_default(
        health.get("mcm_computed_ok"),
        default=str(mcm_status).lower() == "computed",
    )
    constraint_summary = _build_constraint_summary(result, health)
    file_summary = _uploaded_file_summary(uploaded_files)

    record = {
        "record_schema": "engineering_decision_record.v1",
        "case_id": _string_or_unknown(case_id),
        "timestamp_utc": _timestamp(timestamp_utc),
        "engineering_mode": _string_or_unknown(engineering_mode or activation.get("mode") or help_type),
        "help_type": _string_or_unknown(help_type or engineering_mode or activation.get("mode")),
        "problem_statement": _truncate_text(problem_statement, MAX_TEXT_CHARS),
        "model_id": _string_or_unknown(model_id),
        "activation_1_json": _compact_activation_1(activation_1_json),
        "mcm_required": bool(mcm_required),
        "mcm_request_summary": _summarize_mcm_request(request_obj),
        "mcm_status": _string_or_unknown(mcm_status).lower(),
        "mcm_computed_ok": bool(mcm_computed_ok),
        "mcm_run_health": _compact_mcm_run_health(health, mcm_required),
        "mcm_result_summary": _summarize_mcm_result(result),
        "constraint_summary": constraint_summary,
        "missing_outputs": _compact_list(result.get("missing_outputs") or health.get("missing_outputs"), MAX_LIST_ITEMS),
        "skipped_equations": _compact_skipped_equations(result.get("equations_skipped")),
        "invalid_unit_outputs": _compact_list(result.get("invalid_unit_outputs"), MAX_LIST_ITEMS),
        "unit_warnings": _compact_list(result.get("unit_warnings"), MAX_LIST_ITEMS),
        "risk_classification": _string_or_unknown(governance.get("risk_classification")),
        "human_review_required": _bool_or_default(governance.get("human_review_required"), default=False),
        "governance_status": _string_or_unknown(governance.get("governance_status")),
        "user_facing_status_label": _string_or_unknown(
            governance.get("user_facing_status_label") or governance.get("final_report_status_label")
        ),
        "governance_severity": _string_or_unknown(governance.get("governance_severity")),
        "computation_status": _string_or_unknown(governance.get("computation_status") or mcm_status).lower(),
        "computation_severity": _string_or_unknown(governance.get("computation_severity")),
        "engineering_outcome": _string_or_unknown(governance.get("engineering_outcome")),
        "engineering_outcome_label": _string_or_unknown(governance.get("engineering_outcome_label")),
        "engineering_outcome_severity": _string_or_unknown(governance.get("engineering_outcome_severity")),
        "governance_reasons": _compact_list(governance.get("governance_reasons"), MAX_LIST_ITEMS),
        "final_report_status_label": _string_or_unknown(governance.get("final_report_status_label")),
        "final_report_text": _truncate_text(final_report_text, MAX_TEXT_CHARS) if final_report_text is not None else None,
        "uploaded_file_names": file_summary["uploaded_file_names"],
        "uploaded_files": file_summary["uploaded_files"],
    }
    return _json_safe(record)


def validate_engineering_decision_record(record: Any) -> dict:
    """Return validation diagnostics without raising."""

    errors = []
    warnings = []
    if not isinstance(record, dict):
        return {
            "valid": False,
            "errors": ["Engineering Decision Record must be a JSON object."],
            "warnings": [],
        }

    required_fields = (
        "case_id",
        "timestamp_utc",
        "engineering_mode",
        "help_type",
        "problem_statement",
        "mcm_required",
        "mcm_status",
        "mcm_computed_ok",
        "mcm_run_health",
        "constraint_summary",
        "risk_classification",
        "human_review_required",
        "governance_status",
        "governance_reasons",
        "final_report_status_label",
        "uploaded_file_names",
    )
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required EDR field: {field}.")

    known_mcm_statuses = {
        "computed",
        "partial",
        "needs_human_review",
        "unsupported",
        "error",
        "not_required",
        "unknown",
    }
    mcm_status = str(record.get("mcm_status") or UNKNOWN).lower()
    if mcm_status not in known_mcm_statuses:
        warnings.append(f"Unknown MCM status: {mcm_status}.")

    known_governance_statuses = {
        "not_required",
        "computed_criteria_passed",
        "computed_selection_pass",
        "computed_with_failure",
        "computed_with_unknowns",
        "computed_screening_pass",
        "computed_screening_no_viable_option",
        "computed_diagnostic_result",
        "partial",
        "needs_human_review",
        "unsupported",
        "error",
        "unknown",
    }
    governance_status = str(record.get("governance_status") or UNKNOWN).lower()
    if governance_status not in known_governance_statuses:
        warnings.append(f"Unknown governance status: {governance_status}.")

    if not isinstance(record.get("constraint_summary", {}), dict):
        errors.append("constraint_summary must be an object.")
    if not isinstance(record.get("uploaded_file_names", []), list):
        errors.append("uploaded_file_names must be a list.")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def summarize_engineering_decision_record(record: Any) -> dict:
    """Return a compact UI/API-safe EDR summary."""

    rec = _as_dict(record)
    constraint_summary = _as_dict(rec.get("constraint_summary"))
    health = _as_dict(rec.get("mcm_run_health"))
    summary = {
        "case_id": rec.get("case_id") or UNKNOWN,
        "timestamp_utc": rec.get("timestamp_utc") or UNKNOWN,
        "engineering_mode": rec.get("engineering_mode") or rec.get("help_type") or UNKNOWN,
        "help_type": rec.get("help_type") or rec.get("engineering_mode") or UNKNOWN,
        "mcm_required": _bool_or_default(rec.get("mcm_required"), default=False),
        "mcm_status": rec.get("mcm_status") or UNKNOWN,
        "mcm_computed_ok": _bool_or_default(rec.get("mcm_computed_ok"), default=False),
        "governance_status": rec.get("governance_status") or UNKNOWN,
        "user_facing_status_label": rec.get("user_facing_status_label") or rec.get("final_report_status_label") or UNKNOWN,
        "governance_severity": rec.get("governance_severity") or UNKNOWN,
        "computation_status": rec.get("computation_status") or rec.get("mcm_status") or UNKNOWN,
        "computation_severity": rec.get("computation_severity") or UNKNOWN,
        "engineering_outcome": rec.get("engineering_outcome") or UNKNOWN,
        "engineering_outcome_label": rec.get("engineering_outcome_label") or UNKNOWN,
        "engineering_outcome_severity": rec.get("engineering_outcome_severity") or UNKNOWN,
        "final_report_status_label": rec.get("final_report_status_label") or UNKNOWN,
        "risk_classification": rec.get("risk_classification") or UNKNOWN,
        "human_review_required": _bool_or_default(rec.get("human_review_required"), default=False),
        "constraint_summary": {
            "total": _safe_int(constraint_summary.get("total")),
            "passed": _safe_int(constraint_summary.get("passed")),
            "failed": _safe_int(constraint_summary.get("failed")),
            "unknown": _safe_int(constraint_summary.get("unknown")),
            "overall_pass": constraint_summary.get("overall_pass"),
            "screening_status": constraint_summary.get("screening_status") or health.get("screening_status"),
            "screening_overall_pass": constraint_summary.get("screening_overall_pass"),
            "rejected_candidate_failures": _compact_list(
                constraint_summary.get("rejected_candidate_failures")
                or health.get("rejected_candidate_failures"),
                8,
            ),
            "rejected_option_failures": _compact_list(
                constraint_summary.get("rejected_option_failures")
                or health.get("rejected_option_failures"),
                8,
            ),
            "rejected_alternative_failures": _compact_list(
                constraint_summary.get("rejected_alternative_failures")
                or health.get("rejected_alternative_failures"),
                8,
            ),
            "selected_candidate_failures": _compact_list(
                constraint_summary.get("selected_candidate_failures")
                or health.get("selected_candidate_failures"),
                8,
            ),
            "selected_configuration_key": (
                constraint_summary.get("selected_configuration_key")
                or health.get("selected_configuration_key")
            ),
            "blocking_failures": _compact_list(constraint_summary.get("blocking_failures"), 8),
        },
        "mcm_run_health": {
            "readiness_label": health.get("readiness_label") or UNKNOWN,
            "equations_executed_count": _safe_int(health.get("equations_executed_count")),
            "equations_skipped_count": _safe_int(health.get("equations_skipped_count")),
            "missing_variables_count": _safe_int(health.get("missing_variables_count")),
            "missing_outputs_count": _safe_int(health.get("missing_outputs_count")),
            "invalid_unit_outputs_count": _safe_int(health.get("invalid_unit_outputs_count")),
            "unit_warnings_count": _safe_int(health.get("unit_warnings_count")),
            "selection_status": health.get("selection_status") or UNKNOWN,
            "selected_configuration_label": health.get("selected_configuration_label"),
            "selected_config_label": health.get("selected_config_label"),
            "selected_solution": health.get("selected_solution"),
            "selected_solution_pass": health.get("selected_solution_pass"),
            "selected_conductor_AWG": health.get("selected_conductor_AWG"),
            "selected_power_supply_A": health.get("selected_power_supply_A"),
            "selected_fuse_A": health.get("selected_fuse_A"),
            "rejected_option_failures": _compact_list(health.get("rejected_option_failures"), 8),
            "selected_candidate_failures": _compact_list(health.get("selected_candidate_failures"), 8),
            "selected_configuration_key": health.get("selected_configuration_key"),
            "selected_candidate_key": health.get("selected_candidate_key"),
            "viable_candidates": _compact_list(health.get("viable_candidates"), 8),
            "viable_non_selected_alternatives": _compact_list(
                health.get("viable_non_selected_alternatives"),
                8,
            ),
            "selected_option_margin_sensitive_warnings": _compact_list(
                health.get("selected_option_margin_sensitive_warnings"),
                8,
            ),
            "screening_status": health.get("screening_status") or UNKNOWN,
            "viable_candidates_count": _safe_int(health.get("viable_candidates_count")),
            "rejected_candidates_count": _safe_int(health.get("rejected_candidates_count")),
            "selected_candidate_all_criteria_pass": health.get("selected_candidate_all_criteria_pass"),
            "diagnostic_status": health.get("diagnostic_status") or UNKNOWN,
            "primary_root_cause": health.get("primary_root_cause") or UNKNOWN,
            "supported_root_cause_flags": _compact_list(health.get("supported_root_cause_flags"), 8),
            "eliminated_cause_flags": _compact_list(health.get("eliminated_cause_flags"), 8),
            "unresolved_cause_flags": _compact_list(health.get("unresolved_cause_flags"), 8),
            "diagnostic_evidence_count": _safe_int(health.get("diagnostic_evidence_count")),
        },
        "missing_outputs_count": len(_as_list(rec.get("missing_outputs"))),
        "skipped_equations_count": len(_as_list(rec.get("skipped_equations"))),
        "invalid_unit_outputs_count": len(_as_list(rec.get("invalid_unit_outputs"))),
        "unit_warnings_count": len(_as_list(rec.get("unit_warnings"))),
        "uploaded_file_names": _compact_list(rec.get("uploaded_file_names"), MAX_LIST_ITEMS),
    }
    return _json_safe(summary)


def safe_json_dumps(record: Any, *, indent: int | None = 2) -> str:
    """Dump JSON defensively, tolerating non-serializable fields."""

    try:
        return json.dumps(
            _json_safe(record),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
            allow_nan=False,
        )
    except Exception:
        return json.dumps(
            str(record),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )


def _compact_activation_1(value: Any) -> dict:
    activation = _as_dict(value)
    if not activation:
        if value in (None, ""):
            return {"status": "missing"}
        return {
            "status": "non_object",
            "type": type(value).__name__,
            "preview": _truncate_text(value, MAX_SUMMARY_TEXT_CHARS),
        }
    return {
        "workflow_version": activation.get("workflow_version") or UNKNOWN,
        "mcm_required": _bool_or_default(activation.get("mcm_required"), default=False),
        "mcm_invocation_type": activation.get("mcm_invocation_type") or UNKNOWN,
        "mode": activation.get("mode") or UNKNOWN,
        "problem_type": activation.get("problem_type") or UNKNOWN,
        "objective": _truncate_text(activation.get("objective"), MAX_SUMMARY_TEXT_CHARS),
        "routing_reason": _truncate_text(activation.get("routing_reason"), MAX_SUMMARY_TEXT_CHARS),
        "qualitative_plan": _compact_list(activation.get("qualitative_plan"), 12),
        "safety_flags": _compact_list(activation.get("safety_flags"), 12),
        "missing_information": _compact_list(activation.get("missing_information"), 12),
        "schema_normalization_diagnostics": _compact_list(activation.get("schema_normalization_diagnostics"), 12),
        "mcm_request_summary": _summarize_mcm_request(activation.get("mcm_request")),
    }


def _summarize_mcm_request(value: Any) -> dict:
    request = _as_dict(value)
    if not request:
        return {"status": "missing"}
    equations = _as_list(request.get("equations"))
    variables = request.get("variables") if isinstance(request.get("variables"), dict) else {}
    solve_for = _as_list(request.get("solve_for"))
    return {
        "status": "available",
        "computation_id": request.get("computation_id") or UNKNOWN,
        "mode": request.get("mode") or UNKNOWN,
        "problem_type": request.get("problem_type") or UNKNOWN,
        "objective": _truncate_text(request.get("objective"), MAX_SUMMARY_TEXT_CHARS),
        "equation_count": len(equations),
        "variable_count": len(variables),
        "solve_for_count": len(solve_for),
        "solve_for": _compact_list(solve_for, MAX_LIST_ITEMS),
        "constraint_count": len(_as_list(request.get("constraints"))),
        "assumption_count": len(_as_list(request.get("assumptions"))),
        "missing_variables": _compact_list(request.get("missing_variables"), MAX_LIST_ITEMS),
        "document_signal_count": len(_as_list(request.get("document_signals"))),
        "document_role_note_count": len(_as_list(request.get("document_role_notes"))),
        "load_allocation_note_count": len(_as_list(request.get("load_allocation_notes"))),
        "notes_for_mcm": _compact_list(request.get("notes_for_mcm"), 12),
    }


def _compact_mcm_run_health(health: dict, mcm_required: bool) -> dict:
    if not health:
        return {
            "mcm_required": bool(mcm_required),
            "mcm_status": "not_required" if not mcm_required else UNKNOWN,
            "mcm_computed_ok": False,
            "readiness_label": "not_required" if not mcm_required else UNKNOWN,
        }
    allowed_keys = (
        "mcm_required",
        "mcm_status",
        "mcm_computed_ok",
        "mcm_status_label",
        "mcm_status_severity",
        "equations_executed_count",
        "equations_skipped_count",
        "missing_variables_count",
        "missing_outputs_count",
        "invalid_unit_outputs_count",
        "unit_warnings_count",
        "constraint_total",
        "constraint_passed",
        "constraint_failed",
        "constraint_unknown",
        "overall_release_status",
        "overall_recommendation_status",
        "recommended_option_name",
        "recommended_concept_name",
        "selected_solution",
        "selection_status",
        "selected_solution_pass",
        "selected_configuration_label",
        "selected_config_label",
        "selected_conductor_AWG",
        "selected_power_supply_A",
        "selected_fuse_A",
        "rejected_option_failures",
        "rejected_alternative_failures",
        "selected_candidate_failures",
        "selected_configuration_key",
        "selected_candidate_key",
        "viable_candidates",
        "viable_non_selected_alternatives",
        "selected_option_margin_sensitive_warnings",
        "blocking_failures",
        "screening_status",
        "viable_candidates_count",
        "rejected_candidates_count",
        "selected_candidate_all_criteria_pass",
        "rejected_candidate_failures",
        "diagnostic_status",
        "supported_root_cause_flags",
        "eliminated_cause_flags",
        "unresolved_cause_flags",
        "primary_root_cause",
        "diagnostic_evidence_count",
        "diagnostic_categories",
        "readiness_label",
    )
    compact = {key: health.get(key) for key in allowed_keys if key in health}
    compact["mcm_required"] = _bool_or_default(compact.get("mcm_required"), default=bool(mcm_required))
    compact["selected_conductor_AWG"] = _first_non_missing_selection_value(
        compact.get("selected_conductor_AWG"),
        health.get("selected_conductor_AWG"),
        health.get("selected_conductor_awg"),
    )
    compact["selected_power_supply_A"] = _first_non_missing_selection_value(
        compact.get("selected_power_supply_A"),
        health.get("selected_power_supply_A"),
        health.get("selected_power_supply_rating_A"),
        health.get("selected_ps_rating_A"),
        health.get("selected_ps_amps"),
        health.get("selected_ps_A"),
    )
    compact["selected_fuse_A"] = _first_non_missing_selection_value(
        compact.get("selected_fuse_A"),
        health.get("selected_fuse_A"),
        health.get("selected_fuse_rating_A"),
        health.get("selected_fuse_amps"),
    )
    if _is_missing_selection_value(compact.get("selected_solution")):
        compact["selected_solution"] = _selection_component_label(compact)
    if compact.get("selection_status") == "selection_pass" and compact.get("selected_solution_pass") is None:
        compact["selected_solution_pass"] = True
    compact["blocking_failures"] = _compact_list(compact.get("blocking_failures"), 12)
    compact["rejected_option_failures"] = _compact_list(compact.get("rejected_option_failures"), 12)
    compact["rejected_alternative_failures"] = _compact_list(compact.get("rejected_alternative_failures"), 12)
    compact["selected_candidate_failures"] = _compact_list(compact.get("selected_candidate_failures"), 12)
    compact["viable_candidates"] = _compact_list(compact.get("viable_candidates"), 12)
    compact["viable_non_selected_alternatives"] = _compact_list(
        compact.get("viable_non_selected_alternatives"),
        12,
    )
    compact["selected_option_margin_sensitive_warnings"] = _compact_list(
        compact.get("selected_option_margin_sensitive_warnings"),
        12,
    )
    compact["rejected_candidate_failures"] = _compact_list(compact.get("rejected_candidate_failures"), 12)
    compact["supported_root_cause_flags"] = _compact_list(compact.get("supported_root_cause_flags"), 12)
    compact["eliminated_cause_flags"] = _compact_list(compact.get("eliminated_cause_flags"), 12)
    compact["unresolved_cause_flags"] = _compact_list(compact.get("unresolved_cause_flags"), 12)
    compact["diagnostic_categories"] = _compact_list(compact.get("diagnostic_categories"), 12)
    return _json_safe(compact)


def _first_non_missing_selection_value(*values: Any) -> Any:
    for value in values:
        if not _is_missing_selection_value(value):
            return value
    return None


def _is_missing_selection_value(value: Any) -> bool:
    if value in (None, ""):
        return True
    if isinstance(value, str) and value.strip().lower() in {"unknown", "null", "none", "n/a", "na"}:
        return True
    return False


def _selection_component_label(health: dict) -> str | None:
    conductor = health.get("selected_conductor_AWG")
    power_supply = health.get("selected_power_supply_A")
    fuse = health.get("selected_fuse_A")
    if any(_is_missing_selection_value(value) for value in (conductor, power_supply, fuse)):
        return None
    return f"conductor={conductor} AWG; power_supply={power_supply} A; fuse={fuse} A"


def _summarize_mcm_result(result: dict) -> dict:
    if not result:
        return {"status": "missing"}
    outputs = result.get("outputs") if isinstance(result.get("outputs"), dict) else {}
    output_summary = {}
    for name, output in list(outputs.items())[:MAX_LIST_ITEMS]:
        if isinstance(output, dict):
            output_summary[str(name)] = {
                "value": _safe_scalar(output.get("value")),
                "unit": output.get("unit") or UNKNOWN,
                "source": output.get("source") or output.get("result_status") or UNKNOWN,
                "status": output.get("status") or output.get("result_status") or UNKNOWN,
            }
        else:
            output_summary[str(name)] = {"value": _safe_scalar(output), "unit": UNKNOWN}
    return {
        "status": result.get("status") or UNKNOWN,
        "message": _truncate_text(result.get("message"), MAX_SUMMARY_TEXT_CHARS),
        "computation_id": result.get("computation_id") or UNKNOWN,
        "objective": _truncate_text(result.get("objective"), MAX_SUMMARY_TEXT_CHARS),
        "output_count": len(outputs),
        "output_keys": _compact_list(list(outputs.keys()), MAX_LIST_ITEMS),
        "outputs": output_summary,
        "diagnostics": _compact_list(result.get("diagnostics"), 12),
    }


def _build_constraint_summary(result: dict, health: dict) -> dict:
    checks = result.get("constraint_checks") if isinstance(result.get("constraint_checks"), dict) else {}
    summary = checks.get("summary") if isinstance(checks.get("summary"), dict) else {}
    if not summary:
        summary = {
            "total": health.get("constraint_total"),
            "passed": health.get("constraint_passed"),
            "failed": health.get("constraint_failed"),
            "unknown": health.get("constraint_unknown"),
            "blocking_failures": health.get("blocking_failures"),
        }
    blocking_failures = summary.get("blocking_failures")
    if health.get("screening_status") == "screening_pass" or health.get("selection_status") in {
        "selection_pass",
        "selected_option_failed_criteria",
        "selection_unknown",
        "selection_no_viable_option",
    }:
        blocking_failures = health.get("blocking_failures")
    return {
        "total": _safe_int(summary.get("total")),
        "passed": _safe_int(summary.get("passed")),
        "failed": _safe_int(summary.get("failed")),
        "unknown": _safe_int(summary.get("unknown")),
        "overall_pass": summary.get("overall_pass"),
        "screening_status": health.get("screening_status"),
        "screening_overall_pass": True if health.get("screening_status") == "screening_pass" else None,
        "rejected_candidate_failures": _compact_list(health.get("rejected_candidate_failures"), 12),
        "selection_status": health.get("selection_status"),
        "selection_overall_pass": True if health.get("selection_status") == "selection_pass" else None,
        "rejected_option_failures": _compact_list(health.get("rejected_option_failures"), 12),
        "rejected_alternative_failures": _compact_list(health.get("rejected_alternative_failures"), 12),
        "selected_candidate_failures": _compact_list(health.get("selected_candidate_failures"), 12),
        "selected_configuration_key": health.get("selected_configuration_key"),
        "selected_candidate_key": health.get("selected_candidate_key"),
        "viable_non_selected_alternatives": _compact_list(
            health.get("viable_non_selected_alternatives"),
            12,
        ),
        "blocking_failures": _compact_list(blocking_failures, 12),
        "margin_sensitive_passes": _compact_list(summary.get("margin_sensitive_passes"), 12),
        "notes": _compact_list(summary.get("notes"), 12),
    }


def _compact_skipped_equations(value: Any) -> list:
    items = []
    for item in _as_list(value)[:MAX_LIST_ITEMS]:
        if isinstance(item, dict):
            items.append({
                "equation": _truncate_text(item.get("equation") or item.get("expression") or item.get("name"), MAX_SUMMARY_TEXT_CHARS),
                "reason": _truncate_text(item.get("reason") or item.get("message"), MAX_SUMMARY_TEXT_CHARS),
            })
        else:
            items.append(_truncate_text(item, MAX_SUMMARY_TEXT_CHARS))
    return _json_safe(items)


def _uploaded_file_summary(uploaded_files: Any) -> dict:
    files = []
    names = []
    for item in _as_list(uploaded_files):
        if isinstance(item, dict):
            name = _first_non_empty(item.get("display_name"), item.get("filename"), item.get("name"), UNKNOWN)
            entry = {
                "display_name": _string_or_unknown(name),
                "mime_type": _string_or_unknown(item.get("mime_type")),
            }
            if item.get("sha256"):
                entry["sha256"] = _string_or_unknown(item.get("sha256"))
            if item.get("hash"):
                entry["hash"] = _string_or_unknown(item.get("hash"))
            if item.get("temp_path"):
                entry["temp_path"] = _string_or_unknown(item.get("temp_path"))
            if item.get("path"):
                entry["path"] = _string_or_unknown(item.get("path"))
        else:
            name = os.path.basename(str(item)) if item is not None else UNKNOWN
            entry = {
                "display_name": _string_or_unknown(name),
                "path": _string_or_unknown(item),
            }
        names.append(entry["display_name"])
        files.append(entry)
    return {
        "uploaded_file_names": names,
        "uploaded_files": files,
    }


def _compact_list(value: Any, max_items: int) -> list:
    items = _as_list(value)
    compact = []
    for item in items[:max_items]:
        if isinstance(item, dict):
            compact.append(_compact_dict(item))
        else:
            compact.append(_truncate_text(item, MAX_SUMMARY_TEXT_CHARS))
    if len(items) > max_items:
        compact.append(f"... {len(items) - max_items} additional item(s) omitted")
    return _json_safe(compact)


def _compact_dict(value: dict) -> dict:
    preferred = (
        "name",
        "type",
        "item",
        "equation",
        "expression",
        "message",
        "reason",
        "status",
        "severity",
        "margin",
        "margin_percent",
    )
    keys = [key for key in preferred if key in value]
    if not keys:
        keys = list(value.keys())[:8]
    return {
        str(key): _truncate_text(value.get(key), MAX_SUMMARY_TEXT_CHARS)
        if not isinstance(value.get(key), (int, float, bool, type(None)))
        else _safe_scalar(value.get(key))
        for key in keys
    }


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value, key=str)
    if isinstance(value, dict):
        return [value]
    if isinstance(value, str):
        return [value] if value else []
    try:
        return list(value)
    except TypeError:
        return [value]


def _bool_or_default(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    if value is None:
        return bool(default)
    return bool(value)


def _safe_int(value: Any) -> int:
    try:
        if value is None or value == "":
            return 0
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return _truncate_text(value, MAX_SUMMARY_TEXT_CHARS)


def _string_or_unknown(value: Any) -> str:
    text = str(value).strip() if value is not None else ""
    return text or UNKNOWN


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _truncate_text(value: Any, max_chars: int) -> str:
    if value is None:
        return ""
    text = str(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 24] + "... [truncated]"


def _timestamp(value: Any) -> str:
    if isinstance(value, datetime.datetime):
        dt = value.astimezone(datetime.UTC)
        return dt.isoformat().replace("+00:00", "Z")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")


def _json_safe(value: Any, depth: int = 0, seen: set[int] | None = None) -> Any:
    if seen is None:
        seen = set()
    if depth > 12:
        return _truncate_text(value, MAX_SUMMARY_TEXT_CHARS)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, datetime.datetime):
        return value.astimezone(datetime.UTC).isoformat().replace("+00:00", "Z")
    obj_id = id(value)
    if obj_id in seen:
        return "[circular]"
    if isinstance(value, dict):
        seen.add(obj_id)
        safe = {
            str(key): _json_safe(item, depth + 1, seen)
            for key, item in list(value.items())[:200]
        }
        seen.discard(obj_id)
        return safe
    if isinstance(value, (list, tuple, set)):
        seen.add(obj_id)
        safe = [_json_safe(item, depth + 1, seen) for item in list(value)[:200]]
        seen.discard(obj_id)
        return safe
    return _truncate_text(value, MAX_SUMMARY_TEXT_CHARS)
