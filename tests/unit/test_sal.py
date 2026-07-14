# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from sos.sal import normalize_interpretation, normalize_json

pytestmark = pytest.mark.unit


def test_sal_accepts_exact_json_object() -> None:
    result = normalize_json('{"status":"ok","value":3}', required_fields={"status"})

    assert result.valid is True
    assert result.value == {"status": "ok", "value": 3}
    assert result.normalized is False


def test_sal_removes_only_one_outer_json_fence() -> None:
    result = normalize_json('```json\n{"status": "ok"}\n```')

    assert result.valid is True
    assert result.normalized is True


def test_sal_does_not_extract_json_from_prose_or_guess_repairs() -> None:
    result = normalize_json('model says {"status":"ok"}')

    assert result.valid is False
    assert result.value is None
    assert result.issues == ("invalid_json",)


def test_sal_reports_missing_required_fields_without_discarding_valid_object() -> None:
    result = normalize_json({"classification": "focused"}, required_fields={"summary"})

    assert result.valid is False
    assert result.value == {"classification": "focused"}
    assert result.issues == ("missing_required_field:summary",)


def test_sal_rejects_nonfinite_numbers_and_nonobject_roots() -> None:
    assert normalize_json('{"value": NaN}').issues == ("invalid_json",)
    assert normalize_json("[1, 2, 3]").issues == ("root_must_be_object",)


def test_sal_enforces_depth_and_size_bounds() -> None:
    deep = {"a": {"b": {"c": 1}}}
    too_deep = normalize_json(deep, max_depth=1)
    too_large = normalize_json({"a": 1, "b": 2}, max_items=1)

    assert too_deep.valid is False
    assert too_deep.issues == ("maximum JSON depth exceeded",)
    assert too_large.issues == ("maximum JSON object size exceeded",)


def test_interpretation_envelope_requires_classification_and_summary() -> None:
    accepted = normalize_interpretation({"classification": "background", "summary": "synthetic"})
    rejected = normalize_interpretation({"classification": "background"})

    assert accepted.valid is True
    assert rejected.issues == ("missing_required_field:summary",)
