<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: industrial_exhaust_airflow_pack
pack_name: Industrial Exhaust Airflow Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: exhaust, duct, airflow, cfm, fan, static pressure, fpm, round duct, duct velocity, duct diameter, ventilation, hood, air volume

## Scope

Industrial exhaust and ventilation airflow sizing, duct velocity checks, round
duct area calculations, candidate duct diameter screening, fan and static
pressure context, and source-based airflow constraints.

## Expected Document Roles

- airflow requirement or design flow
- duct geometry or standard duct size table
- maximum or target duct velocity criteria
- fan/static pressure limits when provided
- field notes describing installed routing or constraints

## Canonical Units

- airflow: cfm
- velocity: fpm
- diameter: in
- area: ft^2
- pressure: in w.g. or Pa when source documents provide it

## Safe Equation Patterns

- diameter_ft = diameter_in / 12.0
- radius_ft = diameter_ft / 2.0
- area_sq_ft = PI_VALUE * (radius_ft ** 2)
- velocity_fpm = airflow_cfm / area_sq_ft
- candidate_pass = velocity_fpm <= maximum_allowed_velocity_fpm

## Constraint Patterns

Compare computed duct velocity to the stated maximum or target velocity. Select
the minimum acceptable standard diameter only when all governing hard criteria
pass.

## Common Failure Modes

Undersized duct, excessive velocity, missing standard-size table, missing fan
static-pressure check, unsupported assumptions about installed duct routing, and
confusing diameter/radius inch-to-foot conversion.

## MCM Routing Guidance

Use deterministic MCM for duct area, velocity, diameter candidate screening,
and pass/fail velocity checks. Keep fan pressure or hood capture conclusions
partial unless the needed source values are present.

## Human-Review Triggers

Missing exhaust classification, hazardous material constraints, unknown fan
curve/static pressure margin, code-required capture velocity, or field routing
changes not represented in the supplied evidence.

## Reporting Guidance

Use exhaust/airflow language only when grounded in the problem or artifacts.
Report selected duct size, computed velocity, checked velocity criteria, and
whether fan/static pressure was outside scope or missing.

## Evidence-Basis Guidance

Tie conclusions to user airflow, uploaded duct/criteria documents, MCM-computed
area and velocity outputs, pass/fail criteria, and missing fan/static-pressure
or routing information.

## Forbidden Cross-Domain Language

Do not mention remote panel voltage, conductor sizing, AWG, fuse coordination,
inrush current, terminal losses, connector losses, or power supply sizing unless
those terms appear in the user problem or supplied artifacts.
