# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Generate byte-auditable evidence from the included EAS implementation."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from eas.workflow import EngineeringWorkflow  # noqa: E402
from shared.version import __version__  # noqa: E402

CASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = CASE_DIR / "input.json"
OUTPUT_DIR = CASE_DIR / "generated"
PACKAGED_MANIFEST_PATH = ROOT / "src" / "carter" / "evidence" / "manifest.json"
COMMAND = "python -m examples.evidence.run_case"


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def build_artifacts(input_payload: Mapping[str, Any]) -> dict[str, bytes]:
    result = EngineeringWorkflow().run(input_payload)
    checks = {
        "workflow_advisory_ready": result.get("status") == "advisory_ready",
        "schema_valid": result["schema_validation"]["valid"] is True,
        "mcm_computed": result["mcm"]["result"]["status"] == "computed",
        "human_review_required": result["human_review_required"] is True,
        "governance_bounded": (result["governance"]["governance_status"] == "needs_human_review"),
        "mock_planning_backend": (result["stage_one_plan"]["planning_backend"]["kind"] == "mock"),
        "no_language_model": (
            result["stage_one_plan"]["planning_backend"]["is_language_model"] is False
        ),
        "synthetic_fixture": (
            result["normalized_request"]["fixture_id"] == "synthetic_thermal_enclosure_v1"
        ),
    }
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise RuntimeError("Evidence checks failed: " + ", ".join(failures))

    structured_plan = {
        "schema": "evidence.structured_plan.v1",
        "planning_contract": "probabilistic_stage_one",
        "actual_backend": result["stage_one_plan"]["planning_backend"],
        "probabilistic_boundary_exercised": False,
        "plan": result["stage_one_plan"],
    }
    computation = {
        "schema": "evidence.deterministic_computation.v1",
        **result["mcm"],
    }
    governance = {
        "schema": "evidence.governance.v1",
        **result["governance"],
    }
    final_response = {
        "schema": "evidence.final_response.v1",
        **result["advisory"],
    }
    execution_metadata = {
        "schema": "evidence.execution_metadata.v1",
        "software_version": __version__,
        "python_version": platform.python_version(),
        "execution_timestamp": input_payload["timestamp_utc"],
        "timestamp_source": "fixed_synthetic_fixture",
        "model_backend": "mock",
        "language_model_invoked": False,
        "deterministic": True,
        "probabilistic": False,
        "network_access": False,
        "paid_api_used": False,
        "fixture_id": input_payload["fixture_id"],
        "embedded_checks": {
            "collected": len(checks),
            "passed": sum(checks.values()),
            "failed": len(failures),
            "details": checks,
        },
        "repository_test_status": (
            "Not run by the evidence command; see PUBLIC_RELEASE_REPORT.md."
        ),
        "command": COMMAND,
    }
    execution_record = {
        "schema": "evidence.continuous_execution.v1",
        "user_input": dict(input_payload),
        "normalized_request": result["normalized_request"],
        "structured_plan": structured_plan,
        "schema_validation": result["schema_validation"],
        "deterministic_computation": computation,
        "governance": governance,
        "final_response": final_response,
        "execution_metadata": execution_metadata,
    }
    response_markdown = "\n".join(
        [
            "# Synthetic Engineering Advisory",
            "",
            str(result["advisory"]["summary"]),
            "",
            "## Governance Status",
            "",
            str(result["governance"]["final_report_status_label"]),
            "",
            "## Professional Boundary",
            "",
            str(result["professional_boundary"]),
            "",
            "All input values are synthetic and are not suitable for design use.",
            "",
        ]
    ).encode("utf-8")

    return {
        "01_user_input.json": canonical_bytes(dict(input_payload)),
        "02_normalized_request.json": canonical_bytes(result["normalized_request"]),
        "03_structured_plan.json": canonical_bytes(structured_plan),
        "04_schema_validation.json": canonical_bytes(result["schema_validation"]),
        "05_deterministic_computation.json": canonical_bytes(computation),
        "06_governance.json": canonical_bytes(governance),
        "07_final_response.json": canonical_bytes(final_response),
        "07_final_response.md": response_markdown,
        "08_execution_metadata.json": canonical_bytes(execution_metadata),
        "09_continuous_execution.json": canonical_bytes(execution_record),
    }


def manifest_for(
    input_bytes: bytes,
    artifacts: Mapping[str, bytes],
    input_payload: Mapping[str, Any],
) -> dict[str, Any]:
    metadata = json.loads(artifacts["08_execution_metadata.json"])
    return {
        "schema": "evidence.manifest.v1",
        "software_version": __version__,
        "python_version": platform.python_version(),
        "execution_timestamp": input_payload["timestamp_utc"],
        "timestamp_source": "fixed_synthetic_fixture",
        "input_hash": digest(input_bytes),
        "output_hashes": {name: digest(content) for name, content in sorted(artifacts.items())},
        "test_status": metadata["embedded_checks"],
        "model_backend": "mock",
        "language_model_invoked": False,
        "deterministic": True,
        "probabilistic": False,
        "regeneration_command": COMMAND,
    }


def generate(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    input_bytes = INPUT_PATH.read_bytes()
    input_payload = json.loads(input_bytes)
    if not isinstance(input_payload, dict):
        raise TypeError("Evidence input must be a JSON object")
    artifacts = build_artifacts(input_payload)
    manifest = manifest_for(input_bytes, artifacts, input_payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        (output_dir / name).write_bytes(content)
    manifest_bytes = canonical_bytes(manifest)
    (output_dir / "manifest.json").write_bytes(manifest_bytes)
    if output_dir.resolve() == OUTPUT_DIR.resolve():
        PACKAGED_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        PACKAGED_MANIFEST_PATH.write_bytes(manifest_bytes)
    return manifest


def _semantic_artifact(name: str, content: bytes) -> bytes:
    """Remove only runtime-version metadata before cross-version comparison."""

    if name not in {"08_execution_metadata.json", "09_continuous_execution.json"}:
        return content
    value = json.loads(content)
    if name == "08_execution_metadata.json":
        value.pop("python_version", None)
    else:
        value["execution_metadata"].pop("python_version", None)
    return canonical_bytes(value)


def check(output_dir: Path = OUTPUT_DIR) -> bool:
    input_bytes = INPUT_PATH.read_bytes()
    input_payload = json.loads(input_bytes)
    expected_artifacts = build_artifacts(input_payload)
    required = set(expected_artifacts) | {"manifest.json"}
    missing = sorted(name for name in required if not (output_dir / name).is_file())
    if missing:
        print("Evidence files missing: " + ", ".join(missing), file=sys.stderr)
        return False

    stored = {name: (output_dir / name).read_bytes() for name in required}
    if output_dir.resolve() == OUTPUT_DIR.resolve() and (
        not PACKAGED_MANIFEST_PATH.is_file()
        or PACKAGED_MANIFEST_PATH.read_bytes() != stored["manifest.json"]
    ):
        print("Packaged evidence manifest differs from checked evidence.", file=sys.stderr)
        return False
    stored_manifest = json.loads(stored.pop("manifest.json"))
    failures: list[str] = []

    if stored_manifest.get("input_hash") != digest(input_bytes):
        failures.append("input_hash")
    stored_hashes = stored_manifest.get("output_hashes")
    if not isinstance(stored_hashes, dict) or set(stored_hashes) != set(stored):
        failures.append("output_hash_set")
    else:
        failures.extend(
            f"output_hash:{name}"
            for name, content in sorted(stored.items())
            if stored_hashes.get(name) != digest(content)
        )

    for name, expected in expected_artifacts.items():
        if _semantic_artifact(name, stored[name]) != _semantic_artifact(name, expected):
            failures.append(f"semantic_content:{name}")

    expected_manifest = manifest_for(input_bytes, expected_artifacts, input_payload)
    for manifest in (stored_manifest, expected_manifest):
        manifest.pop("python_version", None)
        manifest.pop("output_hashes", None)
    if stored_manifest != expected_manifest:
        failures.append("manifest_metadata")

    if failures:
        print("Evidence check failed: " + ", ".join(failures), file=sys.stderr)
        return False
    print(
        "Evidence is self-consistent and semantically reproducible; "
        "runtime Python metadata is preserved from the generation run."
    )
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify checked artifacts without rewriting them.",
    )
    args = parser.parse_args(argv)
    if args.check:
        return 0 if check() else 1
    manifest = generate()
    print(f"Generated {len(manifest['output_hashes'])} evidence artifacts in {OUTPUT_DIR}")
    print("Input SHA-256: " + manifest["input_hash"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
