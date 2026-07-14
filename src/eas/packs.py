# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Discovery and deterministic selection of first-party engineering packs."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from .modes import EngineeringMode, normalize_mode

DEFAULT_PACK_ROOT = Path(__file__).resolve().parent / "engineering_packs"


@dataclass(frozen=True)
class EngineeringPack:
    pack_id: str
    category: str
    relative_path: str
    title: str
    sha256: str

    def public_dict(self) -> dict[str, str]:
        return asdict(self)


_MODE_PACKS = {
    EngineeringMode.SOLVE_PROBLEM: "modes/solve_problem_pack",
    EngineeringMode.DIAGNOSE_ROOT_CAUSE: "modes/diagnose_root_cause_pack",
    EngineeringMode.REVIEW_DESIGN: "modes/review_design_pack",
    EngineeringMode.SUGGEST_IMPROVEMENTS: "modes/suggest_improvements_pack",
    EngineeringMode.EXPLORE_NOVEL_SOLUTION: "modes/explore_novel_solution_pack",
}

_DOMAIN_RULES = (
    ("aerospace_aerodynamics_pack", ("aerodynamic", "airfoil", "wing", "drag", "lift coefficient")),
    ("domains/aerospace_preliminary_design_pack", ("aircraft", "aerospace", "flight", "fuselage")),
    ("domains/compressed_air_pneumatics_pack", ("compressed air", "pneumatic", "compressor")),
    (
        "domains/dc_controls_power_pack",
        ("dc power", "24vdc", "direct current", "control panel", "voltage drop"),
    ),
    (
        "domains/industrial_exhaust_airflow_pack",
        ("exhaust", "ventilation", "duct", "airflow", "fan"),
    ),
    (
        "domains/software_systems_engineering_pack",
        ("software", "api", "service", "database", "latency"),
    ),
    ("fluid_pump_loop_pack", ("pump", "hydraulic", "fluid", "pipe", "head loss", "flow rate")),
    (
        "mechanical_power_transmission_pack",
        ("gear", "gearbox", "shaft", "bearing", "belt", "chain", "torque"),
    ),
    (
        "structural_mechanical_bracket_pack",
        ("structural", "bracket", "beam", "fastener", "stress", "deflection"),
    ),
    (
        "thermal_enclosure_cooling_pack",
        ("thermal", "temperature", "cooling", "heat", "enclosure", "chiller"),
    ),
    ("core_release_assessment_pack", ("release assessment", "readiness", "acceptance criteria")),
    ("core_release_pack", ("release", "verification", "validation plan")),
)


def discover_packs(pack_root: Path | str | None = None) -> dict[str, EngineeringPack]:
    root = Path(pack_root or DEFAULT_PACK_ROOT).resolve()
    registry: dict[str, EngineeringPack] = {}
    if not root.is_dir():
        return registry
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        pack_id = relative[:-3]
        content = path.read_bytes()
        registry[pack_id] = EngineeringPack(
            pack_id=pack_id,
            category=relative.split("/", 1)[0] if "/" in relative else "domain",
            relative_path=relative,
            title=_first_heading(content.decode("utf-8", errors="replace"), path.stem),
            sha256=hashlib.sha256(content).hexdigest(),
        )
    return registry


def select_packs(
    mode: EngineeringMode | str,
    problem_statement: str,
    domain: str = "",
    *,
    pack_root: Path | str | None = None,
) -> list[EngineeringPack]:
    registry = discover_packs(pack_root)
    normalized_mode = normalize_mode(mode)
    selected_ids: list[str] = []
    mode_pack = _MODE_PACKS[normalized_mode]
    if mode_pack in registry:
        selected_ids.append(mode_pack)

    corpus = f"{domain} {problem_statement}".lower()
    for pack_id, keywords in _DOMAIN_RULES:
        if pack_id in registry and any(keyword in corpus for keyword in keywords):
            selected_ids.append(pack_id)

    return [registry[item] for item in _dedupe(selected_ids)]


def load_pack_text(pack: EngineeringPack, pack_root: Path | str | None = None) -> str:
    """Load a registry-resolved pack without accepting arbitrary paths."""

    root = Path(pack_root or DEFAULT_PACK_ROOT).resolve()
    candidate = (root / pack.relative_path).resolve()
    if root not in candidate.parents or not candidate.is_file():
        raise ValueError("Engineering pack path escaped the configured registry.")
    return candidate.read_text(encoding="utf-8")


def _first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()[:200]
    return fallback.replace("_", " ").title()


def _dedupe(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
