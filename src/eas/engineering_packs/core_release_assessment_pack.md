<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Core Release Assessment Pack

Pack id: core_release_assessment
Pack type: EAS engineering guidance
Version: 0.1
Formula policy: This pack is not a formula library and does not define
domain-specific equations.

Apply this pack when the user asks whether a design, package, skid, cabinet,
bracket, subsystem, component, or installation is ready for engineering
release, fabrication, installation, acceptance, or review-design approval.

## A. Purpose

Guide EAS Activation 1 and final reporting for engineering release-assessment
and review-design workflows.

The pack should help EAS preserve document roles, extract acceptance criteria,
prepare deterministic MCM requests when calculations are required, and report
release status without overstating certainty.

## B. Scope

This pack covers general release assessment only. It applies across domains
when supporting documents define inputs, limits, and acceptance criteria.

It does not replace domain-specific codes, sealed engineering judgment, FEA,
CFD, detailed code compliance, vendor-certified analysis, or final PE approval.
Domain-specific formulas belong in later domain packs or in source documents
provided for the job.

## C. Document-Role Handling

Activation 1 should identify and preserve the role of each source. Expected
roles include:

- engineering request or problem statement
- load schedule, process requirements, or design inputs
- datasheets or equipment ratings
- field notes or installation notes
- acceptance criteria
- exclusions or assumptions
- test reports or measurements

Use `document_role_notes` to explain how each role was used. If a document has
more than one role, state each role explicitly.

## D. Source Priority And No-Double-Counting Rules

Use acceptance criteria as the source of pass/fail thresholds.

Use datasheets as the source of rated capacities and limits.

Use schedules, process requirements, bills of load, or demand tables as the
source of aggregate design loads, flows, demands, losses, or required capacity.

Use field notes, installation notes, commissioning notes, and local
measurements as the source of geometry, routing, installation context, and
local or specific calculation inputs.

Do not add two values together if they may represent the same physical load,
flow, loss, current, heat load, or demand. If overlap is possible, add a
`document_role_notes` or `load_allocation_notes` entry explaining which source
was used and why.

If ambiguity materially affects pass/fail and cannot be resolved from the
provided sources, mark the affected criterion `UNKNOWN` or flag
`needs_human_review` rather than silently double-counting.

## E. MCM-Routing Rules

Use deterministic MCM when:

- numerical calculations are needed
- acceptance criteria require pass/fail checks
- margin or threshold comparison is needed
- unit-bearing calculations are present
- release status depends on computed values

Do not require MCM for purely qualitative summaries, document inventories, or
cases where required documents and numeric inputs are missing and no bounded
calculation can be formed.

## F. MCM-Safe Equation Grammar

Activation 1 should emit only equations of this form:

`<single_variable> = <safe_expression>`

Every comparison must be assigned to an output variable. Do not emit a bare
comparison such as `a <= b` as the whole expression.

Allowed expression patterns:

- arithmetic with `+`, `-`, `*`, `/`, and `**` for exponentiation
- comparisons: `<=`, `>=`, `<`, `>`, `==`, `!=`
- boolean logic: `and`, `or`, `not`
- `if(condition, true_value, false_value)`
- `any_null([a, b, c])`
- `piecewise(condition1, value1, condition2, value2, default)`
- `piecewise_select(...)` only if MCM normalizes it
- string statuses: `"PASS"`, `"FAIL"`, `"UNKNOWN"`

Avoid:

- prose equations
- `sum(... for all rows)` unless expanded into explicit row variables
- unit tokens inside expressions such as `40 degC:` or `5 ft:`
- `^` for exponentiation; use `**`
- implicit variables not listed in `variables`
- unbounded formulas requiring unknown coefficients or lookup curves

For candidate-specific criteria, keep candidate identity tokens consistent
within each candidate-local criterion and aggregate. Do not mix identifiers such
as `A_P3` with `C_P3` or `B_P2` with `C_P2` inside the same candidate aggregate.

## G. Criterion Naming Conventions

Prefer numbered criterion outputs:

- `criterion_C1_pass`
- `criterion_C2_pass`
- `criterion_C3_pass`

Descriptive equivalents are also acceptable when they are clearer:

- `flow_criterion_pass`
- `head_capacity_criterion_pass`
- `temperature_rise_criterion_pass`

Each criterion equation should map to one acceptance criterion. Each criterion
output should be boolean when possible.

Use an explicit final status expression. Pattern:

`overall_release_status = if(any_null([criterion_C1_pass, criterion_C2_pass]), "UNKNOWN", if(criterion_C1_pass and criterion_C2_pass, "PASS", "FAIL"))`

If all criteria are known and any criterion fails, the result is a computed
failure:

- `status = computed`
- `overall_release_status = "FAIL"`

## H. Computed FAIL Policy

A deterministic failed criterion is a valid computed engineering result. Do not
downgrade the result to `needs_human_review` just because one or more criteria
fail.

Use `needs_human_review` for missing required inputs, unresolved
contradictions, unsupported calculations, unsafe assumptions, material source
ambiguity, or domain requirements outside the current computation capability.

## I. Constraint Summary Expectations

MCM should produce or support final reporting of:

- total criteria count
- passed count
- failed count
- unknown count
- `overall_pass` boolean or null
- blocking failures
- margins where numeric comparator checks are available
- margin-sensitive pass warnings when margin is small

These summary items should be treated as deterministic computation artifacts
when MCM status is `computed`.

## J. Margin-Sensitive Pass Guidance

If a criterion passes with small positive margin, flag it as cautionary, not
failing.

Default small-margin threshold may be `<=10%` unless the repository or source
documents define another threshold.

Recommended language:

- passes but margin-sensitive
- operational verification recommended
- do not change pass/fail solely because margin is small

## K. Final Engineering Advisory Report Guidance

The final report should include:

- executive summary
- primary recommendation
- evidence and computed values
- criterion-by-criterion pass/fail
- overall release status
- risk and uncertainty handling
- immediate next step
- missing information that would materially change the answer

The report should not overstate precision. It should preserve MCM-computed
values when status is `computed`. It should clearly separate computed findings
from assumptions, cautions, and qualitative engineering judgment.

## L. Unsupported Or Incomplete Computation Handling

If MCM status is not `computed`:

- do not invent missing numeric outputs
- do not make unsupported pass/fail declarations
- explain what blocked computation
- identify missing or contradictory inputs
- recommend the next verification step

If release status depends on missing or contradictory inputs, report
`UNKNOWN` or `needs_human_review` rather than forcing PASS or FAIL.
