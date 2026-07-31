# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Verify the complete public experience from an isolated installed wheel."""

from __future__ import annotations

import argparse
import json
import os
import site
import sys
import sysconfig
from importlib import import_module, metadata, resources
from pathlib import Path
from zoneinfo import TZPATH, ZoneInfo, ZoneInfoNotFoundError

EXPECTED_STEPS = (
    "environment",
    "metadata",
    "health",
    "session",
    "carter_chat",
    "eas",
    "sis",
    "csc_hearing",
    "csc_transcript",
    "csc_interpretation",
    "evidence",
    "templates_static",
    "license",
    "engineering_packs",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _assert_installed_imports(checkout_root: Path) -> None:
    purelib = Path(sysconfig.get_paths()["purelib"]).resolve()
    checkout_src = (checkout_root / "src").resolve()
    for entry in sys.path:
        candidate = Path(entry or os.curdir).resolve()
        _require(
            candidate != checkout_src and checkout_src not in candidate.parents,
            f"checkout source directory is importable: {candidate}",
        )
    for package_name in ("carter", "csc", "eas", "shared", "sis", "sos"):
        module_path = Path(import_module(package_name).__file__ or "").resolve()
        _require(
            module_path.is_relative_to(purelib),
            f"{package_name} resolved outside isolated site-packages: {module_path}",
        )


def _assert_no_iana_data() -> None:
    _require(TZPATH == (), f"expected empty zoneinfo search path, found {TZPATH!r}")
    try:
        metadata.distribution("tzdata")
    except metadata.PackageNotFoundError:
        pass
    else:
        raise AssertionError("tzdata must not be installed in the isolated environment")

    try:
        ZoneInfo("UTC")
    except ZoneInfoNotFoundError:
        return
    raise AssertionError("ZoneInfo('UTC') unexpectedly succeeded without IANA data")


def _assert_response(response, *, label: str, expected_status: int = 200) -> dict:
    _require(
        response.status_code == expected_status,
        f"{label} returned HTTP {response.status_code}: {response.get_data(as_text=True)!r}",
    )
    data = response.get_json()
    _require(isinstance(data, dict), f"{label} did not return a JSON object")
    return data


def run(checkout_root: Path) -> tuple[str, ...]:
    completed: list[str] = []
    _require(site.ENABLE_USER_SITE is False, "user site-packages must be disabled")
    _assert_installed_imports(checkout_root)
    _assert_no_iana_data()
    completed.append("environment")

    import carter
    from carter.web import create_app
    from eas.packs import discover_packs
    from shared.config import load_settings

    distribution = metadata.distribution("carter-synthetic-os")
    _require(carter.__version__ == "0.1.0", f"unexpected package version: {carter.__version__}")
    _require(
        distribution.version == "0.1.0", f"unexpected metadata version: {distribution.version}"
    )
    _require(
        distribution.metadata.get("License-Expression") == "AGPL-3.0-only",
        "wheel metadata does not declare AGPL-3.0-only",
    )
    completed.append("metadata")

    client = create_app(
        load_settings({"CARTER_PROVIDER": "mock"}),
        testing=True,
    ).test_client()
    health = _assert_response(client.get("/health"), label="health")
    _require(
        health
        == {
            "network_checked": False,
            "provider": "mock",
            "status": "ok",
            "version": "0.1.0",
        },
        f"unexpected health response: {health!r}",
    )
    completed.append("health")

    session = _assert_response(client.get("/api/session"), label="session")
    csrf_token = session.get("csrf_token")
    _require(isinstance(csrf_token, str) and csrf_token, "session did not provide a CSRF token")
    headers = {"X-CSRF-Token": csrf_token}
    completed.append("session")

    chat = _assert_response(
        client.post(
            "/api/chat",
            json={"prompt": "Run the isolated Windows UTC wheel smoke."},
            headers=headers,
        ),
        label="Carter chat",
    )
    _require(chat["provider"]["name"] == "mock", "Carter chat did not use the mock provider")
    _require(chat["memory"]["persistent"] is False, "Carter chat unexpectedly used persistence")
    completed.append("carter_chat")

    eas = _assert_response(
        client.post(
            "/api/eas/run",
            json={
                "fixture_id": "synthetic_thermal_enclosure_v1",
                "problem_statement": "Evaluate the synthetic enclosure fixture.",
                "mode": "review-design",
            },
            headers=headers,
        ),
        label="EAS",
    )
    _require(
        eas["computation"]["result"]["status"] == "computed",
        "EAS did not complete deterministic computation",
    )
    completed.append("eas")

    sis = _assert_response(
        client.post(
            "/api/sis/run",
            json={
                "fixture_id": "synthetic_inspection_scheduler_v1",
                "problem_statement": "Generate a synthetic inspection candidate.",
                "mode": "system-architecture",
            },
            headers=headers,
        ),
        label="SIS",
    )
    _require(
        sis["status"] == "hypothesis_requires_independent_review",
        "SIS did not return the governed review status",
    )
    completed.append("sis")

    hearing = _assert_response(
        client.post("/api/csc/hearing", json={"active": True}, headers=headers),
        label="CSC hearing",
    )
    _require(hearing["state"]["hearing_active"] is True, "CSC hearing did not activate")
    completed.append("csc_hearing")

    transcript = _assert_response(
        client.post(
            "/api/csc/transcript",
            json={
                "transcript": "Carter, inspect the synthetic evidence.",
                "speech_detected": True,
            },
            headers=headers,
        ),
        label="CSC transcript",
    )
    _require(transcript["event"]["attention"] == "focused", "CSC transcript was not focused")
    completed.append("csc_transcript")

    interpretation = _assert_response(
        client.post("/api/csc/interpret", json={}, headers=headers),
        label="CSC interpretation",
    )
    _require(
        interpretation["interpretation"]["governed"] is True,
        "CSC interpretation was not governed",
    )
    _require(
        interpretation["interpretation"]["authorizes_response"] is False,
        "CSC interpretation unexpectedly authorized a response",
    )
    completed.append("csc_interpretation")

    manifest_text = (
        resources.files("carter").joinpath("evidence", "manifest.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(manifest_text)
    _require(manifest["software_version"] == "0.1.0", "packaged evidence version is incorrect")
    _require(manifest["deterministic"] is True, "packaged evidence is not deterministic")
    completed.append("evidence")

    package_root = resources.files("carter")
    for relative_path in (
        ("templates", "index.html"),
        ("templates", "license.html"),
        ("static", "app.js"),
        ("static", "styles.css"),
    ):
        resource = package_root.joinpath(*relative_path)
        _require(resource.is_file(), f"missing packaged resource: {'/'.join(relative_path)}")
    for path in ("/", "/static/app.js", "/static/styles.css"):
        response = client.get(path)
        _require(response.status_code == 200, f"packaged route failed: {path}")
    completed.append("templates_static")

    license_text = package_root.joinpath("legal", "LICENSE").read_text(encoding="utf-8")
    _require(
        "GNU AFFERO GENERAL PUBLIC LICENSE" in license_text,
        "packaged AGPL license text is missing",
    )
    license_response = client.get("/license")
    _require(license_response.status_code == 200, "packaged license route failed")
    _require(
        "GNU AFFERO GENERAL PUBLIC LICENSE" in license_response.get_data(as_text=True),
        "license route omitted the AGPL text",
    )
    completed.append("license")

    packs = discover_packs()
    _require(len(packs) == 18, f"expected 18 engineering-pack files, found {len(packs)}")
    _require(
        all(pack.sha256 and len(pack.sha256) == 64 for pack in packs.values()),
        "engineering-pack inventory contains an invalid hash",
    )
    completed.append("engineering_packs")

    _require(tuple(completed) == EXPECTED_STEPS, f"installed-wheel steps were skipped: {completed}")
    return tuple(completed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout-root", type=Path, required=True)
    args = parser.parse_args()
    completed = run(args.checkout_root.resolve())
    print("INSTALLED_WHEEL_SMOKE=PASS")
    print("STEPS=" + ",".join(completed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
