<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# EAS Engineering Packs

Engineering packs are thin guidance layers for the Engineer Assistance System
(EAS). They describe reusable workflow behavior, source handling, reporting
expectations, and MCM-safe planning rules.

Packs are not formula libraries, answer banks, or hardcoded test fixtures.
Domain formulas and code-specific calculations should live in future domain
packs only when they are general, validated, and reusable.

Current packs:

- `core_release_pack.md` - core EAS v2 source handling, deterministic MCM
  routing, evidence-basis, and reporting discipline.
- `core_release_assessment_pack.md` - legacy core release-assessment guidance
  retained as a fallback.
- `modes/solve_problem_pack.md`
- `modes/review_design_pack.md`
- `modes/diagnose_root_cause_pack.md`
- `modes/suggest_improvements_pack.md`
- `modes/explore_novel_solution_pack.md`
- `domains/industrial_exhaust_airflow_pack.md`
- `domains/dc_controls_power_pack.md`
- `mechanical_power_transmission_pack.md`

Future TODO:

- Add domain packs for electrical, structural, fluid, thermal, controls, or
  other specialties only when they provide general domain policy and equations,
  not one-off answers for existing tests.
