# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from sos.computation import mcm
from sos.computation.mcm import process

pytestmark = pytest.mark.unit


def synthetic_sum_request() -> dict:
    return {
        "computation_id": "synthetic-unit-test",
        "operation": "sum",
        "variables": {
            "load_a": {"value": 12.0, "unit": "N", "source": "synthetic_fixture"},
            "load_b": {"value": 8.0, "unit": "N", "source": "synthetic_fixture"},
        },
        "requested_output": "combined_load",
        "constraints": [
            {
                "name": "synthetic_individual_limit",
                "lhs": "load_a",
                "comparator": "<=",
                "rhs": 15.0,
                "unit": "N",
            }
        ],
        "sensitivity": {
            "enabled": True,
            "variables": {"load_a": {"percent": 10.0}},
            "outputs": ["combined_load"],
        },
    }


def test_mcm_computes_constraints_units_and_sensitivity() -> None:
    result = process(synthetic_sum_request())
    assert result["status"] == "computed"
    assert result["outputs"]["combined_load"] == pytest.approx(20.0)
    check = result["constraint_checks"]["checks"][0]
    assert check["passes"] is True
    assert check["unit_validation"]["status"] == "valid"
    assert result["constraint_checks"]["summary"]["overall_pass"] is True
    assert result["sensitivity_analysis"]["enabled"] is True
    assert result["sensitivity_analysis"]["cases"][0]["varied_input"] == "load_a"
    assert result["mcm_run_health"]["mcm_computed_ok"] is True


def test_mcm_rejects_unsafe_expression_without_execution() -> None:
    result = process(
        {
            "expression": "__import__('os').system('echo unsafe')",
            "inputs": {},
            "requested_output": "unsafe",
        }
    )
    assert result["status"] == "unsupported"
    assert "could not be evaluated safely" in result["message"]
    assert result["outputs"] == {}


@pytest.mark.parametrize(
    "expression",
    [
        '"A" * 1000000000',
        "[1] * 1000000000",
        '"%1000000000s" % "A"',
        "['A' * 10000] * 10000",
        "2 ** 1000000000",
        "1e309",
    ],
)
def test_mcm_rejects_unbounded_or_non_finite_expression_results(
    expression: str,
) -> None:
    result = process(
        {
            "expression": expression,
            "inputs": {},
            "requested_output": "bounded_result",
        }
    )

    assert result["status"] == "unsupported"
    assert result["outputs"] == {}
    assert len(repr(result)) < 10000


def test_mcm_rejects_non_finite_operation_inputs() -> None:
    result = process(
        {
            "operation": "sum",
            "inputs": {"invalid": float("nan")},
            "requested_output": "bounded_result",
        }
    )

    assert result["status"] in {"needs_human_review", "unsupported", "error"}
    assert result["outputs"] == {}


def test_mcm_non_finite_string_cannot_pass_constraint_governance() -> None:
    request = synthetic_sum_request()
    request["variables"]["load_a"]["value"] = "NaN"

    result = process(request)

    checks = result.get("constraint_checks", {}).get("checks", [])
    assert not checks or checks[0].get("passes") is not True
    assert result["mcm_run_health"]["mcm_computed_ok"] is False


def test_mcm_missing_required_input_needs_review() -> None:
    result = process(
        {
            "operation": "sum",
            "variables": {
                "missing_value": {
                    "value": None,
                    "unit": "N",
                    "required_for_computation": True,
                }
            },
        }
    )
    assert result["status"] == "needs_human_review"
    assert result["mcm_run_health"]["mcm_computed_ok"] is False


@pytest.mark.parametrize(
    "label",
    ["a", "1", "p12", "12in", "12inches", "12amps", "１２in"],
)
def test_mcm_candidate_labels_preserve_supported_forms(label: str) -> None:
    assert mcm._looks_like_candidate_label_token(label) is True


@pytest.mark.parametrize("label", ["", "ab", "px", "12volt", "12in-extra"])
def test_mcm_candidate_labels_reject_unsupported_forms(label: str) -> None:
    assert mcm._looks_like_candidate_label_token(label) is False


def test_mcm_candidate_label_parser_handles_long_adversarial_input() -> None:
    digits = "9" * 50_000

    assert mcm._looks_like_candidate_label_token(digits + "in") is True
    assert mcm._looks_like_candidate_label_token(digits + "x") is False


@pytest.mark.parametrize(
    ("name", "unit"),
    [
        ("clearance_12in", "in"),
        ("run_12.5ft", "ft"),
        ("run_12..5in", "in"),
        ("clearance_in", "in"),
    ],
)
def test_mcm_dimensional_name_suffixes_preserve_supported_forms(
    name: str,
    unit: str,
) -> None:
    assert mcm._unit_from_name_suffix(name) == unit


@pytest.mark.parametrize("name", ["run_12.ft", "clearance_numeric", "999x"])
def test_mcm_dimensional_name_suffixes_reject_unsupported_forms(name: str) -> None:
    assert mcm._unit_from_name_suffix(name) is None


def test_mcm_dimensional_suffix_parser_handles_long_adversarial_input() -> None:
    digits = "9" * 50_000

    assert mcm._unit_from_name_suffix("length_" + digits + "in") == "in"
    assert mcm._unit_from_name_suffix(digits + "x") is None


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("list[N]", "list[N]"),
        (" array ( kg ) ", "list[kg]"),
        ("vector[text]", "list[string]"),
        ("list( N ]", "list[N]"),
        ("list( )", "list[dimensionless]"),
    ],
)
def test_mcm_list_units_preserve_supported_forms(raw: str, normalized: str) -> None:
    assert mcm.normalize_unit(raw) == normalized


@pytest.mark.parametrize("raw", ["lists[N]", "list[N]junk"])
def test_mcm_list_units_reject_unsupported_wrappers(raw: str) -> None:
    assert mcm.normalize_unit(raw) == raw


def test_mcm_list_unit_parser_handles_long_adversarial_input() -> None:
    spaces = " " * 50_000
    invalid = "list(" + spaces + "x"

    assert mcm.normalize_unit("list[" + spaces + "N]") == "list[N]"
    assert mcm.normalize_unit(invalid) == invalid


@pytest.mark.parametrize(
    ("inner", "normalized", "changed"),
    [
        ("x, else=0", "x, 0", True),
        ("x, ELSE = y + 1", "x, y + 1", True),
        ("x, else =   ", "x, ", True),
        ("else=", "else=", False),
        ("x, otherwise=0", "x, otherwise=0", False),
    ],
)
def test_mcm_piecewise_default_argument_preserves_supported_forms(
    inner: str,
    normalized: str,
    changed: bool,
) -> None:
    assert mcm._normalize_piecewise_inner_default_argument(inner) == (
        normalized,
        changed,
    )


def test_mcm_piecewise_parser_handles_long_adversarial_input() -> None:
    spaces = " " * 50_000

    assert mcm._normalize_piecewise_inner_default_argument("x, else=" + spaces + "0") == (
        "x, 0",
        True,
    )
    unchanged = "x, else" + spaces + "not-an-assignment"
    assert mcm._normalize_piecewise_inner_default_argument(unchanged) == (
        unchanged,
        False,
    )


def test_mcm_internal_exception_details_are_not_returned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exception_detail = "UNIQUE-MCM-SENTINEL C:\\private\\provider\\sentinel.txt"

    def fail(_request: dict) -> str:
        raise RuntimeError(exception_detail)

    monkeypatch.setattr(mcm, "_select_expression", fail)
    result = mcm.process({"expression": "1 + 1"})

    assert result["status"] == "error"
    assert result["message"] == "MCM processing failed."
    assert "UNIQUE-MCM-SENTINEL" not in repr(result)
    assert "C:\\private\\provider\\sentinel.txt" not in repr(result)


class SensitiveMCMError(ValueError):
    pass


_MCM_EXCEPTION_DETAIL = (
    "UNIQUE-MCM-BOUNDARY-SENTINEL Traceback SensitiveMCMError "
    "C:\\private\\provider\\sentinel.txt internal-provider-detail"
)


def _assert_mcm_exception_detail_is_private(result: object) -> None:
    rendered = repr(result)
    for marker in (
        "UNIQUE-MCM-BOUNDARY-SENTINEL",
        "Traceback",
        "SensitiveMCMError",
        "C:\\private\\provider\\sentinel.txt",
        "internal-provider-detail",
    ):
        assert marker not in rendered


def test_mcm_unit_inference_exception_uses_fixed_public_message(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail(*_args, **_kwargs):
        raise SensitiveMCMError(_MCM_EXCEPTION_DETAIL)

    monkeypatch.setattr(mcm, "_infer_unit_node", fail)
    result = mcm.infer_rhs_unit("load + 1", {"load": "N"})

    assert result["message"] == "Unit compatibility was not validated for this expression."
    _assert_mcm_exception_detail_is_private(result)
    assert "UNIQUE-MCM-BOUNDARY-SENTINEL" in caplog.text


def test_mcm_expression_exception_uses_fixed_public_message(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail(*_args, **_kwargs):
        raise SensitiveMCMError(_MCM_EXCEPTION_DETAIL)

    monkeypatch.setattr(mcm, "_safe_eval", fail)
    result = mcm._process_expression(
        {"expression": "load + 1"},
        "load + 1",
        {"load": 2.0},
    )

    assert result["message"] == "Expression could not be evaluated safely."
    _assert_mcm_exception_detail_is_private(result)
    assert "UNIQUE-MCM-BOUNDARY-SENTINEL" in caplog.text


def test_mcm_operation_exception_uses_fixed_public_message(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail(_values):
        raise SensitiveMCMError(_MCM_EXCEPTION_DETAIL)

    monkeypatch.setitem(mcm.SUPPORTED_OPERATIONS, "sum", fail)
    result = mcm._process_operation(
        {"operation": "sum"},
        "sum",
        {"load": 2.0},
    )

    assert result["message"] == "Operation could not be completed."
    _assert_mcm_exception_detail_is_private(result)
    assert "UNIQUE-MCM-BOUNDARY-SENTINEL" in caplog.text


def test_mcm_operation_result_validation_exception_uses_fixed_public_message(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    original = mcm._validate_evaluated_value
    calls = 0

    def fail_on_result(value, depth=0):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise SensitiveMCMError(_MCM_EXCEPTION_DETAIL)
        return original(value, depth)

    monkeypatch.setattr(mcm, "_validate_evaluated_value", fail_on_result)
    result = mcm._process_operation(
        {"operation": "sum"},
        "sum",
        {"load": 2.0},
    )

    assert result["message"] == "Operation result was rejected by the public evaluator."
    _assert_mcm_exception_detail_is_private(result)
    assert "UNIQUE-MCM-BOUNDARY-SENTINEL" in caplog.text


def test_mcm_base_result_validation_exception_uses_fixed_public_message(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail(*_args, **_kwargs):
        raise SensitiveMCMError(_MCM_EXCEPTION_DETAIL)

    monkeypatch.setattr(mcm, "_validate_evaluated_value", fail)
    result = mcm._base_result(
        {},
        status="computed",
        message="Synthetic computed result.",
        outputs={"result": 1.0},
        diagnostics=[],
    )

    assert result["message"] == "MCM rejected an unbounded or non-finite result."
    _assert_mcm_exception_detail_is_private(result)
    assert "UNIQUE-MCM-BOUNDARY-SENTINEL" in caplog.text


def test_mcm_constraint_exception_uses_fixed_public_reason(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail(*_args, **_kwargs):
        raise SensitiveMCMError(_MCM_EXCEPTION_DETAIL)

    monkeypatch.setattr(mcm, "evaluate_constraint", fail)
    result = mcm._evaluate_constraint_spec(
        {"name": "synthetic", "lhs": "load", "comparator": "<=", "rhs": 10},
        {"load": 5.0},
        {"load": "N"},
    )

    assert result["message"] == "Constraint could not be evaluated."
    _assert_mcm_exception_detail_is_private(result)
    assert "UNIQUE-MCM-BOUNDARY-SENTINEL" in caplog.text


def test_mcm_missing_variable_diagnostic_is_derived_from_expression() -> None:
    result = mcm._process_expression(
        {"expression": "missing_load + 1"},
        "missing_load + 1",
        {},
    )

    assert result["message"] == "Expression references variables with no numeric value."
    assert result["diagnostics"] == ["Missing numeric value for variable: missing_load"]


def test_mcm_syntax_validation_does_not_return_parser_exception_message() -> None:
    assert mcm._safe_rhs_expression_error("1 +") == "syntax error"
