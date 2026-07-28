# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""
Deterministic governance gate for EAS engineering decision records.

This module is intentionally dependency-light and defensive. It does not
perform engineering calculations; it classifies decision risk and converts
MCM run state into a bounded governance status for downstream reporting.
"""

from __future__ import annotations

import re
from typing import Any

HIGH_RISK_KEYWORDS = (
    "life safety",
    "structural collapse",
    "pressure vessel",
    "boiler",
    "crane",
    "hoist",
    "rigging",
    "arc flash",
    "hazardous chemical",
    "explosive",
    "fire protection",
    "medical",
    "aviation",
    "public bridge",
    "public infrastructure",
    "code compliance",
    "osha",
    "nec",
    "nfpa",
    "asme",
    "aisc",
    "confined space",
)

MEDIUM_RISK_KEYWORDS = (
    "equipment design review",
    "industrial controls",
    "hydraulics",
    "electrical distribution",
    "production downtime",
    "root cause diagnosis",
    "machinery",
)

SCREENING_MODES = {"suggest-improvements", "explore-novel-solution"}
SELECTION_UNKNOWN_STATUS = "selection_unknown"


LOW_RISK_HINTS = (
    "documentation only",
    "formatting only",
    "grammar only",
    "style only",
    "toy example",
    "training example",
    "conceptual overview",
    "non-engineering",
)


def classify_engineering_risk(
    problem_statement: Any,
    engineering_mode: Any,
    activation_1_json: Any = None,
) -> dict:
    """
    Return a simple rule-based engineering risk classification.

    Default risk is medium for EAS unless the request is clearly low-risk.
    """

    corpus = _risk_corpus(problem_statement, engineering_mode, activation_1_json)
    matched_high = _matched_keywords(corpus, HIGH_RISK_KEYWORDS)
    if matched_high:
        return {
            "risk_classification": "high",
            "risk_reasons": [
                "High-risk engineering category identified: "
                + ", ".join(matched_high)
                + "."
            ],
            "matched_keywords": matched_high,
        }

    matched_medium = _matched_keywords(corpus, MEDIUM_RISK_KEYWORDS)
    if matched_medium:
        return {
            "risk_classification": "medium",
            "risk_reasons": [
                "Medium-risk engineering category identified: "
                + ", ".join(matched_medium)
                + "."
            ],
            "matched_keywords": matched_medium,
        }

    matched_low = _matched_keywords(corpus, LOW_RISK_HINTS)
    if matched_low:
        return {
            "risk_classification": "low",
            "risk_reasons": [
                "Request appears low-risk based on: "
                + ", ".join(matched_low)
                + "."
            ],
            "matched_keywords": matched_low,
        }

    return {
        "risk_classification": "medium",
        "risk_reasons": ["Default EAS risk classification is medium."],
        "matched_keywords": [],
    }


def evaluate_governance(record_or_inputs: Any = None, **inputs: Any) -> dict:
    """
    Evaluate the deterministic governance status for an EDR-like dict.

    Keyword arguments may be supplied as an override/convenience layer.
    """

    record = _as_dict(record_or_inputs)
    if inputs:
        record = {**record, **inputs}

    mcm_required = _as_bool(record.get("mcm_required"))
    mcm_status = _normalize_status(record.get("mcm_status"))
    if not mcm_status and isinstance(record.get("mcm_run_health"), dict):
        mcm_status = _normalize_status(record["mcm_run_health"].get("mcm_status"))
    if not mcm_status and isinstance(record.get("mcm_result_summary"), dict):
        mcm_status = _normalize_status(record["mcm_result_summary"].get("status"))
    if not mcm_status:
        mcm_status = "not_required" if not mcm_required else "unknown"

    mcm_computed_ok_value = record.get("mcm_computed_ok")
    if mcm_computed_ok_value is None and isinstance(record.get("mcm_run_health"), dict):
        mcm_computed_ok_value = record["mcm_run_health"].get("mcm_computed_ok")
    if mcm_computed_ok_value is None and isinstance(record.get("mcm_result_summary"), dict):
        mcm_computed_ok_value = record["mcm_result_summary"].get("mcm_computed_ok")
    mcm_computed_ok = _as_bool(mcm_computed_ok_value)
    constraint_summary = _constraint_summary(record)
    engineering_mode = _normalize_mode(record.get("engineering_mode") or record.get("help_type"))
    clean_counts = _computed_counts_are_clean(record)
    if not mcm_computed_ok and _is_computed_mcm_status(mcm_status) and clean_counts:
        mcm_computed_ok = True
    screening_viability = _screening_viability(record)
    diagnostic_status = _diagnostic_status(record)
    diagnostic_conclusion = _diagnostic_conclusion(record) or None
    diagnostic_result_status = _diagnostic_result_status(record)
    diagnostic_root_cause_flags = _diagnostic_root_cause_flags(record)
    primary_root_cause = diagnostic_conclusion
    if not primary_root_cause and diagnostic_root_cause_flags:
        primary_root_cause = _diagnostic_root_cause_label(diagnostic_root_cause_flags[0])
    diagnostic_conflict = diagnostic_status == "diagnostic_conflict" or len(diagnostic_root_cause_flags) > 1
    if diagnostic_conflict:
        primary_root_cause = None
    diagnostic_needs_review = (
        diagnostic_status == "diagnostic_needs_human_review"
        or diagnostic_result_status == "NEEDS_HUMAN_REVIEW"
    )
    diagnostic_success = (
        diagnostic_status == "diagnostic_result"
        or _is_known_diagnostic_value(diagnostic_conclusion)
        or len(diagnostic_root_cause_flags) == 1
        or (
            diagnostic_result_status == "ROOT_CAUSE_IDENTIFIED"
            and (bool(primary_root_cause) or len(diagnostic_root_cause_flags) == 1)
        )
    )
    selection_viability = _selection_viability(record)

    risk_result = classify_engineering_risk(
        record.get("problem_statement"),
        engineering_mode or record.get("engineering_mode") or record.get("help_type"),
        record.get("activation_1_json"),
    )
    record_risk = str(record.get("risk_classification") or "").strip().lower()
    risk_classification = _normalize_risk(
        record_risk if record_risk in {"low", "medium", "high"} else risk_result.get("risk_classification")
    )
    risk_reasons = _as_string_list(
        record.get("risk_reasons")
        or record.get("risk_reason")
        or risk_result.get("risk_reasons")
    )

    governance_status = "unknown"
    final_label = "Engineering governance status unknown"
    human_review_required = False
    reasons = []

    if not mcm_required:
        governance_status = "not_required"
        final_label = "AI advisory - deterministic MCM not required"
        human_review_required = risk_classification == "high"
        reasons.append("Deterministic MCM was not required for this EAS request.")
    elif _is_computed_mcm_status(mcm_status) and mcm_computed_ok:
        failed = _count_or_zero(constraint_summary.get("failed"))
        unknown = _count_or_zero(constraint_summary.get("unknown"))
        total = _count_or_zero(constraint_summary.get("total"))
        if engineering_mode in SCREENING_MODES and clean_counts:
            if screening_viability.get("has_viable_candidate"):
                governance_status = "computed_screening_pass"
                final_label = "Computed screening pass"
                reasons.append(
                    "Deterministic screening completed with at least one viable recommendation; failed constraints are treated as rejected-alternative screening results, not selected-recommendation failure."
                )
                if screening_viability.get("selected"):
                    reasons.append(f"Selected recommendation: {screening_viability['selected']}.")
            else:
                governance_status = "computed_screening_no_viable_option"
                final_label = "Deterministic screening computed; no viable option met all criteria"
                reasons.append(
                    "Deterministic screening completed, but no viable candidate or passing recommendation was identified."
                )
        elif engineering_mode == "diagnose-root-cause" and clean_counts and diagnostic_conflict:
            governance_status = "needs_human_review"
            final_label = "Human engineering review required"
            human_review_required = True
            reasons.append(
                "Multiple root-cause flags were supported without a deterministic ranking rule."
            )
        elif engineering_mode == "diagnose-root-cause" and clean_counts and diagnostic_needs_review:
            governance_status = "needs_human_review"
            final_label = "Human engineering review required"
            human_review_required = True
            reasons.append(
                "Deterministic diagnostic logic completed, but the diagnostic result requires human review."
            )
        elif engineering_mode == "diagnose-root-cause" and clean_counts and diagnostic_success:
            governance_status = "computed_diagnostic_result"
            final_label = "Computed \u2014 Root Cause Identified"
            reasons.append(
                "Deterministic diagnostic logic produced a conclusion; failed observed-condition criteria may be diagnostic evidence rather than top-level governance failure."
            )
            if primary_root_cause:
                reasons.append(f"Root cause identified: {primary_root_cause}.")
        elif (
            engineering_mode == "solve-problem"
            and clean_counts
            and selection_viability.get("selection_unknown")
        ):
            governance_status = "needs_human_review"
            final_label = "Human engineering review required"
            human_review_required = True
            reasons.append(
                "Selected solution could not be mapped to candidate-scoped criteria, so the selected-candidate pass/fail status is unknown."
            )
        elif (
            engineering_mode == "solve-problem"
            and clean_counts
            and selection_viability.get("selected_failure")
        ):
            governance_status = "computed_with_failure"
            final_label = "Computed \u2014 Selected Solution Failed"
            reasons.append(
                "Deterministic selection completed, but the selected solution failed one or more required criteria."
            )
        elif (
            engineering_mode == "solve-problem"
            and clean_counts
            and selection_viability.get("selection_pass")
        ):
            governance_status = "computed_selection_pass"
            final_label = "Computed \u2014 Selected Solution Passed"
            reasons.append(
                "Deterministic selection completed; failed or unviable alternatives are separated from viable non-selected alternatives, and the selected solution passed the required hard criteria."
            )
            if selection_viability.get("selected"):
                reasons.append(f"Selected solution: {selection_viability['selected']}.")
        elif (
            engineering_mode == "solve-problem"
            and clean_counts
            and selection_viability.get("no_viable_option")
        ):
            governance_status = "computed_screening_no_viable_option"
            final_label = "Deterministic screening computed; no viable option met all criteria"
            reasons.append(
                "Deterministic solve-problem selection completed, but no viable selected solution was identified."
            )
        elif not clean_counts:
            if engineering_mode in SCREENING_MODES:
                governance_status = "needs_human_review"
                final_label = "Human engineering review required"
            else:
                governance_status = "partial"
                final_label = "Partial deterministic result; do not certify"
            human_review_required = True
            reasons.append(
                "MCM reported computed status, but run-health counts show missing variables, missing outputs, skipped equations, or invalid unit outputs."
            )
        elif failed > 0 and unknown == 0:
            governance_status = "computed_with_failure"
            final_label = _computed_failure_label(engineering_mode)
            reasons.append(
                f"Deterministic MCM completed and {failed} constraint(s) failed."
            )
        elif total > 0 and failed == 0 and unknown == 0:
            governance_status = "computed_criteria_passed"
            final_label = "Deterministic result computed; criteria passed"
            reasons.append("Deterministic MCM completed and all known required constraints passed.")
        else:
            governance_status = "computed_with_unknowns"
            final_label = "Deterministic calculations computed; some criteria unknown"
            reasons.append("Deterministic MCM completed, but constraints are missing or unknown.")
    elif mcm_status == "partial":
        if engineering_mode in SCREENING_MODES:
            governance_status = "needs_human_review"
            final_label = "Human engineering review required"
        else:
            governance_status = "partial"
            final_label = "Partial deterministic result; do not certify"
        human_review_required = True
        reasons.append("MCM returned a partial deterministic result.")
    elif mcm_status == "needs_human_review":
        governance_status = "needs_human_review"
        final_label = "Human engineering review required"
        human_review_required = True
        reasons.append("MCM status requires human engineering review.")
    elif mcm_status == "unsupported":
        governance_status = "unsupported"
        final_label = "Unsupported deterministic computation"
        human_review_required = True
        reasons.append("MCM reported an unsupported deterministic computation.")
    elif mcm_status == "error":
        governance_status = "error"
        final_label = "EAS/MCM system error"
        human_review_required = True
        reasons.append("MCM or EAS reported a system error.")
    elif mcm_status == "computed":
        if not clean_counts:
            if engineering_mode in SCREENING_MODES:
                governance_status = "needs_human_review"
                final_label = "Human engineering review required"
            else:
                governance_status = "partial"
                final_label = "Partial deterministic result; do not certify"
            human_review_required = True
            reasons.append(
                "MCM status was computed, but run-health counts show missing variables, missing outputs, skipped equations, or invalid unit outputs."
            )
        else:
            governance_status = "computed_with_unknowns"
            final_label = "Deterministic calculations computed; some criteria unknown"
            reasons.append("MCM status was computed, but clean-computed health was not confirmed.")
    else:
        governance_status = "needs_human_review"
        final_label = "Human engineering review required"
        human_review_required = True
        reasons.append(f"MCM status '{mcm_status}' is not certifiable by this governance gate.")

    if risk_classification == "high":
        human_review_required = True
        final_label = _human_review_label(final_label)
        if risk_reasons:
            reasons.extend(risk_reasons)
        else:
            reasons.append("High-risk engineering category requires qualified engineer review.")

    reasons = _dedupe_strings(reasons)
    engineering_outcome = _engineering_outcome(governance_status, engineering_mode)
    engineering_outcome_label = _engineering_outcome_label(engineering_outcome, engineering_mode)
    if selection_viability.get("selected_failure"):
        engineering_outcome_label = "Selected solution failed criteria"
    computation_status = _computation_status(mcm_status)
    return {
        "governance_status": governance_status,
        "final_report_status_label": final_label,
        "user_facing_status_label": final_label,
        "governance_severity": _governance_severity(
            governance_status,
            mcm_status,
            bool(mcm_computed_ok),
            clean_counts,
            bool(human_review_required),
        ),
        "computation_status": computation_status,
        "computation_severity": _computation_severity(computation_status),
        "engineering_outcome": engineering_outcome,
        "engineering_outcome_label": engineering_outcome_label,
        "engineering_outcome_severity": _engineering_outcome_severity(engineering_outcome),
        "human_review_required": bool(human_review_required),
        "governance_reasons": reasons,
        "risk_classification": risk_classification,
        "risk_reasons": risk_reasons,
        "mcm_required": bool(mcm_required),
        "mcm_status": mcm_status,
        "mcm_computed_ok": bool(mcm_computed_ok),
        "engineering_mode": engineering_mode or _normalize_mode(record.get("engineering_mode")),
        "selected_solution": selection_viability.get("selected"),
        "selected_configuration_key": selection_viability.get("selected_key"),
        "selected_solution_pass": selection_viability.get("selected_pass"),
        "primary_root_cause": primary_root_cause,
        "constraint_summary": constraint_summary,
    }


def _computed_failure_label(engineering_mode: str) -> str:
    if engineering_mode == "review-design":
        return "Computed — Design Failed Criteria"
    return "Computed — Criteria Failed"


def _is_computed_mcm_status(status: str) -> bool:
    return _normalize_status(status) in {"computed", "computed_clean", "computed_with_warnings"}


def _human_review_label(final_label: str) -> str:
    text = str(final_label or "").strip()
    if "human review" in text.lower():
        return text
    return f"Human Review Required — {text}" if text else "Human Review Required"


def _computation_status(mcm_status: str) -> str:
    status = _normalize_status(mcm_status)
    if _is_computed_mcm_status(status):
        return "computed"
    if status in {"computed", "partial", "needs_human_review", "unsupported", "error"}:
        return status
    if status == "not_required":
        return "not_required"
    return "unknown"


def _computation_severity(computation_status: str) -> str:
    if computation_status in {"computed", "not_required"}:
        return "success"
    if computation_status == "error":
        return "error"
    if computation_status in {"partial", "needs_human_review", "unsupported", "unknown"}:
        return "warning"
    return "unknown"


def _engineering_outcome(governance_status: str, engineering_mode: str) -> str:
    status = str(governance_status or "").strip().lower()
    if status in {"computed_criteria_passed", "computed_selection_pass"}:
        return "pass"
    if status in {"computed_screening_pass"}:
        return "selected_option_pass"
    if status == "computed_with_failure":
        return "fail"
    if status == "computed_screening_no_viable_option":
        return "no_viable_option"
    if status == "computed_diagnostic_result":
        return "root_cause_identified"
    if status == "computed_with_unknowns":
        return "unknown"
    return "unknown"


def _engineering_outcome_label(engineering_outcome: str, engineering_mode: str) -> str:
    if engineering_outcome == "pass":
        if engineering_mode == "solve-problem":
            return "Selected solution passed criteria"
        return "Passed criteria"
    if engineering_outcome == "fail":
        if engineering_mode == "review-design":
            return "Rejected / Failed criteria"
        return "Failed criteria"
    if engineering_outcome == "selected_option_pass":
        return "Selected option passed criteria"
    if engineering_outcome == "no_viable_option":
        return "No viable option"
    if engineering_outcome == "root_cause_identified":
        return "Root cause identified"
    return "Unknown"


def _engineering_outcome_severity(engineering_outcome: str) -> str:
    if engineering_outcome in {"pass", "selected_option_pass", "root_cause_identified"}:
        return "success"
    if engineering_outcome == "fail":
        return "fail"
    if engineering_outcome in {"no_viable_option", "unknown"}:
        return "warning"
    return "unknown"


def _governance_severity(
    governance_status: str,
    mcm_status: str,
    mcm_computed_ok: bool,
    clean_counts: bool,
    human_review_required: bool,
) -> str:
    status = str(governance_status or "").strip().lower()
    mcm = _normalize_status(mcm_status)
    if status == "error" or mcm == "error":
        return "error"
    if human_review_required:
        return "warning"
    if (
        status == "computed_with_failure"
        and _is_computed_mcm_status(mcm)
        and mcm_computed_ok
        and clean_counts
    ):
        return "success"
    if status in {
        "computed_criteria_passed",
        "computed_selection_pass",
        "computed_screening_pass",
        "computed_diagnostic_result",
        "not_required",
    }:
        return "success"
    if status in {
        "computed_with_unknowns",
        "computed_screening_no_viable_option",
        "partial",
        "needs_human_review",
        "unsupported",
        "unknown",
    }:
        return "warning"
    return "unknown"


def summarize_governance(governance_result: Any) -> str:
    """Return a compact, report-ready governance summary string."""

    result = _as_dict(governance_result)
    status = result.get("governance_status") or "unknown"
    label = result.get("final_report_status_label") or "Engineering governance status unknown"
    risk = result.get("risk_classification") or "unknown"
    review = "required" if _as_bool(result.get("human_review_required")) else "not required"
    return f"{label} (governance_status={status}; risk={risk}; human_review={review})."


def _risk_corpus(problem_statement: Any, engineering_mode: Any, activation_1_json: Any) -> str:
    parts = [problem_statement, engineering_mode]
    activation = _as_dict(activation_1_json)
    for key in (
        "problem_type",
        "objective",
        "routing_reason",
        "safety_flags",
        "missing_information",
        "qualitative_plan",
    ):
        parts.append(activation.get(key))
    mcm_request = _as_dict(activation.get("mcm_request"))
    for key in ("problem_type", "objective", "constraints", "notes_for_mcm"):
        parts.append(mcm_request.get(key))
    return " ".join(_flatten_text(parts)).lower()


def _flatten_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, int, float, bool)):
        return [str(value)]
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            items.extend(_flatten_text(key))
            items.extend(_flatten_text(item))
        return items
    try:
        items = []
        for item in value:
            items.extend(_flatten_text(item))
        return items
    except TypeError:
        return [str(value)]


def _matched_keywords(corpus: str, keywords: tuple[str, ...]) -> list[str]:
    matches = []
    for keyword in keywords:
        pattern = r"(?<![a-z0-9])" + re.escape(keyword.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, corpus):
            matches.append(keyword.upper() if keyword in {"osha", "nec", "nfpa", "asme", "aisc"} else keyword)
    return matches


def _constraint_summary(record: dict) -> dict:
    summary = _as_dict(record.get("constraint_summary"))
    health = record.get("mcm_run_health") if isinstance(record.get("mcm_run_health"), dict) else {}
    if not summary and isinstance(record.get("mcm_run_health"), dict):
        summary = {
            "total": health.get("constraint_total"),
            "passed": health.get("constraint_passed"),
            "failed": health.get("constraint_failed"),
            "unknown": health.get("constraint_unknown"),
            "blocking_failures": health.get("blocking_failures"),
        }
    return {
        "total": _count_or_zero(summary.get("total")),
        "passed": _count_or_zero(summary.get("passed")),
        "failed": _count_or_zero(summary.get("failed")),
        "unknown": _count_or_zero(summary.get("unknown")),
        "overall_pass": summary.get("overall_pass"),
        "blocking_failures": _as_list(summary.get("blocking_failures")),
        "rejected_option_failures": _as_list(
            summary.get("rejected_option_failures") or health.get("rejected_option_failures")
        ),
        "rejected_alternative_failures": _as_list(
            summary.get("rejected_alternative_failures") or health.get("rejected_alternative_failures")
        ),
        "selected_candidate_failures": _as_list(
            summary.get("selected_candidate_failures") or health.get("selected_candidate_failures")
        ),
        "viable_non_selected_alternatives": _as_list(
            summary.get("viable_non_selected_alternatives") or health.get("viable_non_selected_alternatives")
        ),
    }


def _computed_counts_are_clean(record: dict) -> bool:
    return (
        _record_count(record, "missing_variables_count", "missing_variables") == 0
        and _record_count(record, "missing_outputs_count", "missing_outputs") == 0
        and _record_count_any(
            record,
            ("equations_skipped_count", "skipped_equations_count"),
            ("equations_skipped", "skipped_equations"),
        ) == 0
        and _record_count(record, "invalid_unit_outputs_count", "invalid_unit_outputs") == 0
    )


def _record_count_any(record: dict, count_keys: tuple[str, ...], list_keys: tuple[str, ...]) -> int:
    for count_key in count_keys:
        for container_key in ("mcm_run_health", "mcm_result_summary"):
            container = record.get(container_key)
            if isinstance(container, dict) and count_key in container:
                return _count_or_zero(container.get(count_key))
        if count_key in record:
            return _count_or_zero(record.get(count_key))
    for list_key in list_keys:
        if list_key in record:
            return len(_as_list(record.get(list_key)))
    return 0


def _record_count(record: dict, count_key: str, list_key: str) -> int:
    for container_key in ("mcm_run_health", "mcm_result_summary"):
        container = record.get(container_key)
        if isinstance(container, dict) and count_key in container:
            return _count_or_zero(container.get(count_key))
    if count_key in record:
        return _count_or_zero(record.get(count_key))
    if list_key in record:
        return len(_as_list(record.get(list_key)))
    return 0


def _screening_viability(record: dict) -> dict:
    selected = _first_non_empty_value(
        record,
        ("recommended_option_name", "selected_solution", "best_candidate", "best_concept_name", "recommended_concept_name"),
    )
    recommendation_status = _normalize_recommendation_status(
        _first_non_empty_value(
            record,
            ("overall_recommendation_status", "recommendation_status", "overall_release_status"),
        )
    )
    passed_count = _first_numeric_value(
        record,
        (
            "passed_concepts_count",
            "passed_options_count",
            "passed_candidates_count",
            "viable_concepts_count",
            "viable_options_count",
            "viable_candidates_count",
        ),
    )
    has_viable_candidate = bool(selected) or recommendation_status == "PASS" or passed_count > 0
    return {
        "has_viable_candidate": has_viable_candidate,
        "selected": selected,
        "overall_recommendation_status": recommendation_status,
        "passed_count": passed_count,
    }


def _diagnostic_conclusion(record: dict) -> str:
    return _first_non_empty_value(
        record,
        (
            "primary_root_cause",
            "overall_root_cause_diagnosis",
            "root_cause_status_string",
            "root_cause",
            "diagnostic_conclusion",
            "diagnosis",
        ),
    )


def _diagnostic_status(record: dict) -> str:
    return str(_value_from_record(record, "diagnostic_status") or "").strip().lower()


def _diagnostic_result_status(record: dict) -> str:
    for name in (
        "overall_diagnostic_result",
        "overall_diagnostic_status",
        "diagnostic_result",
        "root_cause_result",
        "root_cause_status",
    ):
        status = _normalize_diagnostic_result_status(_value_from_record(record, name))
        if status:
            return status
    return ""


def _normalize_diagnostic_result_status(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    token = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").upper()
    if token in {
        "ROOT_CAUSE_IDENTIFIED",
        "CAUSE_IDENTIFIED",
        "DIAGNOSED",
        "DIAGNOSIS_IDENTIFIED",
        "DIAGNOSTIC_RESULT",
    }:
        return "ROOT_CAUSE_IDENTIFIED"
    if token in {
        "NEEDS_HUMAN_REVIEW",
        "HUMAN_REVIEW_REQUIRED",
        "REVIEW_REQUIRED",
        "UNRESOLVED",
        "NO_ROOT_CAUSE_IDENTIFIED",
    }:
        return "NEEDS_HUMAN_REVIEW"
    if token in {"UNKNOWN", "UNDETERMINED", "INDETERMINATE"}:
        return "UNKNOWN"
    return ""


def _diagnostic_root_cause_flags(record: dict) -> list[str]:
    flags = []
    health = record.get("mcm_run_health") if isinstance(record.get("mcm_run_health"), dict) else {}
    for item in _as_list(health.get("supported_root_cause_flags")):
        name = item.get("name") if isinstance(item, dict) else item
        value = item.get("value") if isinstance(item, dict) else True
        if _is_root_cause_flag_name(name) and _as_tristate_bool(value) is True:
            flags.append(str(name))

    for outputs in _diagnostic_output_containers(record):
        for name, raw_value in outputs.items():
            if not _is_root_cause_flag_name(name):
                continue
            if _as_tristate_bool(_unwrap_output_value(raw_value)) is True:
                flags.append(str(name))
    return _dedupe_strings(flags)


def _diagnostic_output_containers(record: dict) -> list[dict]:
    containers = []
    outputs = record.get("outputs")
    if isinstance(outputs, dict):
        containers.append(outputs)
    for key in ("mcm_result", "mcm_result_summary"):
        container = record.get(key)
        if isinstance(container, dict) and isinstance(container.get("outputs"), dict):
            containers.append(container["outputs"])
    return containers


def _is_root_cause_flag_name(name: Any) -> bool:
    lowered = str(name or "").strip().lower()
    if _is_generic_root_cause_rule_flag_name(lowered):
        return False
    return (
        lowered.startswith(("is_root_cause_", "likely_cause_", "probable_cause_", "root_cause_"))
        or "_is_root_cause_" in lowered
        or "_likely_cause_" in lowered
        or "_probable_cause_" in lowered
    )


def _is_generic_root_cause_rule_flag_name(lowered: Any) -> bool:
    lowered = str(lowered or "").strip().lower()
    return bool(re.fullmatch(r"root_cause_(?:rule|logic|criteria?|condition|check).*", lowered))


def _diagnostic_root_cause_label(flag_name: Any) -> str:
    lowered = str(flag_name or "").strip().lower()
    known = {
        "is_root_cause_fouled_strainer": "fouled strainer / excessive strainer pressure drop",
        "likely_cause_fouled_strainer": "fouled strainer / excessive strainer pressure drop",
        "likely_cause_fouled_strainer_filter": "fouled strainer / excessive strainer pressure drop",
        "is_root_cause_restricted_path": "restricted valve or manifold path",
        "is_root_cause_undersized_piping": "undersized or excessively long piping",
        "is_root_cause_tubing_pressure_drop": "excessive tubing pressure drop / undersized actuator tubing",
        "likely_cause_excessive_tubing_pressure_drop": "excessive tubing pressure drop / undersized actuator tubing",
    }
    if lowered in known:
        return known[lowered]
    if lowered.startswith("is_root_cause_"):
        return lowered.removeprefix("is_root_cause_").replace("_", " ")
    return str(flag_name or "")


def _is_known_diagnostic_value(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text not in {
        "",
        "unknown",
        "undetermined",
        "none",
        "n/a",
        "na",
        "null",
        "needs_human_review",
        "human_review_required",
        "review_required",
        "root_cause_identified",
        "no_root_cause_identified",
    }


def _selection_viability(record: dict) -> dict:
    selected = _first_non_empty_value(
        record,
        (
            "selected_solution",
            "selected_solution_name",
            "selected_candidate_key",
            "selected_config_name",
            "selected_configuration_name",
            "selected_configuration_label",
            "selected_config_label",
            "selected_configuration_key",
            "selected_config_key",
            "selected_option_name",
            "selected_candidate_name",
            "selected_concept_name",
            "recommended_config_name",
            "recommended_configuration_name",
            "recommended_configuration_label",
            "recommended_config_label",
            "recommended_option_name",
            "recommended_candidate_name",
            "recommended_solution_name",
            "best_config_label",
            "best_configuration_label",
            "best_config_name",
            "best_candidate_name",
            "best_option_name",
        ),
    )
    selected_components = {
        "conductor": _first_non_missing_value(
            record,
            (
                "selected_conductor_AWG",
                "selected_conductor_awg",
            ),
        ),
        "power_supply": _first_non_missing_value(
            record,
            (
                "selected_power_supply_A",
                "selected_power_supply_rating_A",
                "selected_ps_rating_A",
                "selected_ps_amps",
                "selected_ps_A",
            ),
        ),
        "fuse": _first_non_missing_value(
            record,
            (
                "selected_fuse_A",
                "selected_fuse_rating_A",
                "selected_fuse_amps",
            ),
        ),
    }
    selected_key = _first_non_empty_value(
        record,
        (
            "selected_configuration_key",
            "selected_config_key",
            "selected_candidate_key",
            "selected_option_key",
            "selected_concept_key",
        ),
    )
    if not selected:
        selected = _selection_component_label(selected_components)
    if not selected:
        selected = _generic_selected_solution_value(record)
    if not selected:
        selected = _first_non_empty_value(
            record,
            (
                "selected_conductor_AWG",
                "selected_conductor_awg",
                "selected_power_supply_A",
                "selected_power_supply_rating_A",
                "selected_ps_rating_A",
                "selected_ps_amps",
                "selected_fuse_A",
                "selected_fuse_rating_A",
                "selected_fuse_amps",
            ),
        )
    selected_pass = _first_tristate_bool(
        record,
        (
            "selected_solution_pass",
            "selected_solution_viable",
            "selected_design_pass",
            "selected_option_pass",
            "selected_option_viable",
            "selected_candidate_pass",
            "selected_candidate_viable",
            "selected_config_pass",
            "selected_config_viable",
            "overall_selection_status_pass",
        ),
    )
    selection_status = _first_non_empty_value(
        record,
        (
            "selection_status",
            "overall_selection_status",
            "overall_recommendation_status",
        ),
    )
    selected_metric = _first_non_missing_value(
        record,
        (
            "selected_total_installed_cost",
            "selected_total_installed_cost_USD",
            "selected_total_installed_cost_usd",
            "selected_installed_cost",
            "selected_installed_cost_USD",
            "selected_installed_cost_usd",
            "selected_cost",
            "selected_cost_USD",
            "selected_cost_usd",
            "selected_score",
            "selected_option_score",
            "selected_candidate_score",
            "best_total_installed_cost",
            "best_total_installed_cost_USD",
            "best_total_installed_cost_usd",
            "lowest_cost_among_viable",
            "lowest_cost_among_viable_USD",
            "lowest_cost_among_viable_usd",
        ),
    )
    if selected_pass is None and _selection_status_is_direct_pass(selection_status):
        selected_pass = True
    if selected_pass is None:
        selected_pass = _selection_pass_from_flags(record, selected_components)
    if selected_pass is None:
        selected_pass = _first_tristate_bool(
            record,
            (
            "overall_release_status",
            "overall_result_status",
            "overall_design_pass",
            "overall_selection_pass",
            "overall_selection_status_pass",
            "release_status",
            "overall_status",
        ),
        )
    selected_failures = _selection_selected_failures(record)
    if selected_failures:
        selected_pass = False
    if (
        selected_pass is None
        and _selection_status_indicates_viable_solution(selection_status)
        and not _is_missing_selection_value(selected_metric)
    ):
        selected_pass = True
    selection_status_token = _normalize_selection_status_token(selection_status)
    return {
        "selected": selected,
        "selected_key": selected_key,
        "selected_pass": selected_pass,
        "selection_status": selection_status,
        "selection_pass": bool(selected and selected_pass is True and not selected_failures),
        "selected_failure": bool(selected and selected_pass is False),
        "selection_unknown": bool(selection_status_token == SELECTION_UNKNOWN_STATUS),
        "selected_candidate_failures": selected_failures,
        "no_viable_option": bool(
            not selected
            and _selection_status_indicates_no_viable_option(selection_status)
        ),
    }


def _selection_component_label(components: dict) -> str:
    if any(_is_missing_selection_value(value) for value in components.values()):
        return ""
    return (
        f"conductor={components['conductor']} AWG; "
        f"power_supply={components['power_supply']} A; "
        f"fuse={components['fuse']} A"
    )


def _selection_pass_from_flags(record: dict, components: dict) -> bool | None:
    if any(_is_missing_selection_value(value) for value in components.values()):
        return None

    conductor_pass = _as_tristate_bool(_value_from_record(record, "conductor_selection_pass"))
    ps_pass = _first_tristate_bool(
        record,
        (
            "ps_selection_pass",
            "power_supply_selection_pass",
        ),
    )
    fuse_pass = _as_tristate_bool(_value_from_record(record, "fuse_selection_pass"))
    overall_pass = _first_tristate_bool(
        record,
        (
            "overall_release_status",
            "overall_result_status",
            "overall_design_pass",
            "selected_design_pass",
            "overall_selection_pass",
            "overall_selection_status_pass",
        ),
    )

    flags = (conductor_pass, ps_pass, fuse_pass, overall_pass)
    if any(value is False for value in flags):
        return False
    if all(value is True for value in flags):
        return True
    return None


def _selection_selected_failures(record: dict) -> list:
    failures = []
    for container in _selection_record_containers(record):
        if not isinstance(container, dict):
            continue
        failures.extend(_as_list(container.get("selected_candidate_failures")))
        failures.extend(_as_list(container.get("selected_option_failures")))
    constraint_summary = _as_dict(record.get("constraint_summary"))
    failures.extend(_as_list(constraint_summary.get("selected_candidate_failures")))
    failures.extend(_as_list(constraint_summary.get("selected_option_failures")))
    blocking_failures = _as_list(constraint_summary.get("blocking_failures"))
    for item in blocking_failures:
        if isinstance(item, dict) and str(item.get("type") or "").strip().lower() == "constraint_failure":
            failures.append(item)
    return _dedupe_list_items([item for item in failures if item not in (None, "")])


def _generic_selected_solution_value(record: dict) -> str:
    for container in _selection_record_containers(record):
        if not isinstance(container, dict):
            continue
        for name, value in container.items():
            if _is_generic_selected_solution_field(name):
                unwrapped = _unwrap_output_value(value)
                if not _is_missing_selection_value(unwrapped):
                    return str(unwrapped)
        outputs = container.get("outputs")
        if isinstance(outputs, dict):
            for name, value in outputs.items():
                if _is_generic_selected_solution_field(name):
                    unwrapped = _unwrap_output_value(value)
                    if not _is_missing_selection_value(unwrapped):
                        return str(unwrapped)
    return ""


def _selection_record_containers(record: dict) -> list[dict]:
    containers = [record]
    for key in ("mcm_run_health", "mcm_result_summary", "mcm_result"):
        container = record.get(key)
        if isinstance(container, dict):
            containers.append(container)
    return containers


def _is_generic_selected_solution_field(name: Any) -> bool:
    lowered = str(name or "").strip().lower()
    if not lowered.startswith("selected_"):
        return False
    tokens = {token for token in re.split(r"[^a-z0-9]+", lowered) if token}
    excluded_tokens = {
        "pass",
        "status",
        "margin",
        "warning",
        "warnings",
        "failure",
        "failures",
        "count",
        "cost",
        "price",
        "score",
        "runtime",
        "duration",
        "velocity",
        "speed",
        "flow",
        "airflow",
        "pressure",
        "static",
        "fpm",
    }
    return not tokens.intersection(excluded_tokens)


def _selection_status_is_direct_pass(value: Any) -> bool:
    return _normalize_selection_status_token(value) == "selection_pass"


def _selection_status_indicates_viable_solution(value: Any) -> bool:
    token = _normalize_selection_status_token(value)
    if not token or _selection_status_indicates_no_viable_option(token):
        return False
    return (
        token in {
            "pass",
            "passed",
            "selection_pass",
            "viable_option_found",
            "viable_options_found",
            "viable_solution_found",
            "viable_solutions_found",
            "pass_viable_option_found",
            "pass_viable_solution_found",
            "pass_configuration_selected",
            "configuration_selected",
            "candidate_selected",
            "option_selected",
        }
        or (token.startswith("pass_") and "viable" in token and "found" in token)
        or (token.startswith("pass_") and "selected" in token)
        or ("viable" in token and "found" in token)
    )


def _selection_status_indicates_no_viable_option(value: Any) -> bool:
    token = _normalize_selection_status_token(value)
    if not token:
        return False
    return (
        token in {
            "selection_no_viable_option",
            "no_viable_option",
            "no_viable_options",
            "no_viable_option_found",
            "no_viable_options_found",
            "no_viable_solution",
            "no_viable_solutions",
            "no_viable_solution_found",
            "no_viable_solutions_found",
        }
        or token.startswith("no_viable_")
    )


def _normalize_selection_status_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _first_tristate_bool(record: dict, names: tuple[str, ...]) -> bool | None:
    for name in names:
        value = _as_tristate_bool(_value_from_record(record, name))
        if value is not None:
            return value
    return None


def _as_tristate_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on", "pass", "passed"}:
            return True
        if lowered in {"0", "false", "no", "n", "off", "fail", "failed"}:
            return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 1:
            return True
        if value == 0:
            return False
    return None


def _first_non_missing_value(record: dict, names: tuple[str, ...]) -> Any:
    for name in names:
        value = _value_from_record(record, name)
        if not _is_missing_selection_value(value):
            return value
    return None


def _is_missing_selection_value(value: Any) -> bool:
    if value in (None, ""):
        return True
    if isinstance(value, str) and value.strip().lower() in {"unknown", "null", "none", "n/a", "na"}:
        return True
    return False


def _first_non_empty_value(record: dict, names: tuple[str, ...]) -> str:
    for name in names:
        value = _value_from_record(record, name)
        if value not in (None, ""):
            return str(value)
    return ""


def _first_numeric_value(record: dict, names: tuple[str, ...]) -> int:
    for name in names:
        value = _value_from_record(record, name)
        if value in (None, ""):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _value_from_record(record: dict, name: str) -> Any:
    if name in record:
        return _unwrap_output_value(record.get(name))

    for container_key in ("mcm_run_health", "mcm_result_summary", "mcm_result"):
        container = record.get(container_key)
        if isinstance(container, dict):
            if name in container:
                return _unwrap_output_value(container.get(name))
            outputs = container.get("outputs")
            if isinstance(outputs, dict) and name in outputs:
                return _unwrap_output_value(outputs.get(name))

    outputs = record.get("outputs")
    if isinstance(outputs, dict) and name in outputs:
        return _unwrap_output_value(outputs.get(name))
    return None


def _unwrap_output_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def _normalize_mode(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    aliases = {
        "solve-the-problem": "solve-problem",
        "diagnose-and-solve": "solve-problem",
    }
    return aliases.get(text, text)


def _normalize_recommendation_status(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_risk(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in {"low", "medium", "high"} else "medium"


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _as_string_list(value: Any) -> list[str]:
    return [str(item) for item in _as_list(value) if str(item).strip()]


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _count_or_zero(value: Any) -> int:
    try:
        if value is None or value == "":
            return 0
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _dedupe_strings(items: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _dedupe_list_items(items: list[Any]) -> list[Any]:
    seen = set()
    deduped = []
    for item in items:
        key = repr(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
