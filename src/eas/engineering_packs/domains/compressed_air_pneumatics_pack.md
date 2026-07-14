<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: compressed_air_pneumatics_pack
pack_name: Compressed Air Pneumatics Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: compressed air, pneumatic, pneumatics, purge, purge air, vision purge, air consumption, scfm, cfm, compressor, leak, leakage, enclosure pressure, dewpoint, dew point, dryer, air dryer, labyrinth seal, machine vision, camera enclosure, lens fogging, contamination, pressure drop, air savings, payback

## Scope

Compressed-air consumption reduction, purge-air sizing and reduction,
pneumatic leakage or excessive air use, enclosure purge reliability, dewpoint
and moisture margin, enclosure positive-pressure checks, air-cost savings,
payback, and bounded candidate screening for pneumatic concepts.

## Expected Document Roles

- compressed-air requirements
- baseline air consumption
- candidate concept table
- pneumatic or purge constraints
- dewpoint or moisture requirements
- enclosure pressure requirements
- cost model
- compressor or air-supply limitations
- reliability or contamination constraints

## Canonical Units

- airflow: scfm, cfm
- pressure: psi, inH2O, in_wg
- dewpoint margin: C, degC
- cost: USD
- annual savings: USD/year
- payback: year
- length if needed: ft
- percentage: dimensionless

## Safe Equation Patterns

- total_air_scfm = source_1_scfm + source_2_scfm
- purge_reduction_scfm = baseline_scfm - candidate_scfm
- annual_savings_usd = purge_reduction_scfm * annual_cost_usd_per_scfm
- payback_years = installed_cost_usd / annual_savings_usd
- candidate_viable = purge_pass and dewpoint_pass and pressure_pass and cost_pass
- criterion_pass = candidate_value <= max_allowed_value
- criterion_pass = candidate_value >= min_required_value
- candidate_score = if(candidate_viable, candidate_total_purge_scfm, null)
- selected_concept_name = argmin_label_ignore_null(candidate_labels, candidate_viability_flags, viable_candidates_purge_scfm, viable_candidates_payback_years)

## Constraint Patterns

Check maximum total purge air, minimum dewpoint margin, minimum enclosure
pressure, maximum installed cost, reliability or contamination protection, and
do-not-double-count rules for baseline and candidate purge flows. For candidate
selection, require viability first, then choose lowest air use, then lower
payback if tied.

## Common Failure Modes

Double-counting baseline and candidate purge flows, treating incremental purge
flow as total new flow, using wet or unqualified air where dewpoint margin is
required, ignoring enclosure pressure margin, assuming air savings without a
source cost model, and making reliability or contamination claims without
source evidence.

## MCM Routing Guidance

Use deterministic MCM for purge-flow totals, candidate pass/fail criteria,
air-savings calculations, annual savings, payback, viable-candidate counts, and
selected-concept outputs when source values are present. Keep reliability,
vendor-life, contamination, safety, or code claims partial unless the supplied
evidence supports them.

## Human-Review Triggers

Missing baseline air consumption, missing candidate purge rate, missing
dewpoint or moisture criterion, missing enclosure pressure criterion, missing
cost model when payback is requested, unclear whether candidate purge flow is
total new flow or incremental flow, reliability claims not grounded in supplied
evidence, or safety/code/vendor constraints outside supplied evidence.

## Reporting Guidance

Report the selected concept, baseline air consumption, selected concept air
consumption, net scfm reduction, annual savings, payback, hard requirement
pass/fail checks, rejected alternatives with specific failed criteria,
reliability limitations, and the validation step.

## Evidence-Basis Guidance

Tie conclusions to the candidate table, requirement document, cost model,
MCM-computed savings and payback, hard criteria checked, assumptions, and
missing values.

## Forbidden Cross-Domain Language

Do not mention AWG, fuse, power supply, 24 VDC, conductor, voltage drop, duct
velocity, fan static pressure, or round duct diameter unless those terms appear
in the user problem or supplied artifacts.
