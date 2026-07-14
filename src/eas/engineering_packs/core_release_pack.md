<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: core_release_pack
pack_name: Core Release Pack
pack_type: core
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords:

## Scope

Use this core pack for all active EAS v2 staged workflows. It defines general
source handling, deterministic calculation routing, evidence basis discipline,
and report sanitation expectations.

## Expected Document Roles

- user problem or engineering request
- design inputs, operating requirements, schedules, or process requirements
- equipment ratings, datasheets, or acceptance criteria
- field notes, measurements, or installation context
- assumptions, exclusions, and missing information

## MCM Routing Guidance

Route to deterministic MCM when numeric calculations, unit-bearing equations,
candidate screening, pass/fail criteria, margins, or threshold decisions are
needed. Keep unsupported calculations partial rather than inventing missing
values.

## Reporting Guidance

The final report must summarize the recommendation, decision status, evidence
basis, calculation basis, key calculations, pass/fail checks, limitations,
immediate next step, and material missing information. Do not expose raw JSON,
internal route names, hidden workflow details, or raw pack text.

## Evidence-Basis Guidance

Tie major conclusions to uploaded documents, user-stated values, MCM-computed
outputs, checked criteria, assumptions, missing variables, and governance
status in compact user-facing language.
