<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

pack_id: software_systems_engineering_pack
pack_name: Software Systems Engineering Pack
pack_type: domain
supported_modes: solve-problem, review-design, diagnose-root-cause, suggest-improvements, explore-novel-solution
domain_keywords: software, codebase, code, backend, frontend, Flask, FastAPI, Django, React, JavaScript, TypeScript, Python, API, REST, route, endpoint, auth, session, token, database, schema, JSON, test, unit test, regression, CI, deployment, crash, exception, traceback, log, bug, refactor, security, vulnerability, SSE, job queue, state management, concurrency, timeout, memory leak, software architecture, test failure, stack trace, deployment readiness, security hardening

## Scope

Software engineering analysis involving codebase architecture, backend/frontend
integration, API or service behavior, authentication and session handling, test
failures, regression planning, deployment readiness, logs, exceptions, schema
validation, job or state management, security hardening, and maintainability
review.

## Out Of Scope

Malware creation, credential theft, exploit development, bypassing
authentication, persistence or evasion logic, destructive actions against
third-party systems, production changes without human review, legal/compliance
certification claims, and unverified claims that code is secure or
production-ready.

## Expected Document Roles

- code files
- architecture notes
- implementation reports
- test output
- crash logs
- stack traces
- API specs
- schema definitions
- deployment notes
- security requirements
- acceptance criteria
- regression checklist

## Canonical Units

- time: ms, s
- memory: KB, MB, GB
- size: bytes, KB, MB
- count: dimensionless
- percentage: dimensionless
- status: pass/fail/unknown
- version: string
- severity: low/medium/high/critical

## Safe Equation Patterns

- pass_count = total_tests - failed_tests
- failure_rate = failed_tests / total_tests
- latency_pass = observed_latency_ms <= max_allowed_latency_ms
- payload_size_pass = payload_size_mb <= max_allowed_payload_size_mb
- timeout_pass = observed_runtime_s <= timeout_limit_s
- coverage_pass = coverage_percent >= min_required_coverage_percent
- schema_field_present = not is_null(required_field)
- release_status = if(blocking_failures_count == 0, "PASS", "FAIL")

## Constraint Patterns

- tests must pass
- no known blocking exceptions
- required schema fields must exist
- authenticated routes must enforce auth and session ownership
- user-facing reports must not expose raw secrets, tokens, stack traces, or internal-only metadata
- logs should be redacted
- legacy routes should not be active unless intentionally supported
- regression tests should cover the fixed failure mode
- security-sensitive changes require human review

## Common Failure Modes

Confusing active and legacy routes, trusting unauthenticated request data,
leaking tokens or secrets in reports/logs, treating failing tests as nonblocking,
omitting schema validation, ignoring ownership checks on job/result payloads,
under-testing regression fixes, and claiming deployment readiness without CI,
rollback, or human review evidence.

## MCM Routing Guidance

Use deterministic MCM when there are numeric thresholds, counts, pass/fail
criteria, coverage percentages, latency limits, timeout budgets, memory limits,
or schema completeness checks. Do not use MCM to invent behavior not shown in
code, logs, tests, or supplied reports.

## Human-Review Triggers

Unclear active code path, missing test output, security-sensitive
auth/session/token behavior, production deployment changes, destructive
migration or data deletion, missing rollback plan, incomplete reproduction
steps, failing tests after proposed fix, logs containing secrets or credentials,
ambiguous stack trace or missing code context, and claims of
security/compliance readiness.

## Reporting Guidance

Identify the observed issue, likely root cause, affected files/routes/modules,
evidence basis, recommended fix, regression tests, security/privacy
implications, deployment or rollback notes, remaining risks, and whether human
review is required. Distinguish observed facts from inferred causes and
recommended changes.

## Evidence-Basis Guidance

Tie conclusions to supplied code snippets, file names, stack traces, test
output, implementation reports, logs, architecture documents, and deterministic
checks. Clearly distinguish observed facts from inferred causes and recommended
changes.

## Forbidden Cross-Domain Language

Do not mention AWG, fuse, voltage drop, duct velocity, fan static pressure,
purge scfm, dewpoint, pump head, bracket stress, lift coefficient,
thrust-to-weight, or stall speed unless those terms appear in the user problem
or supplied artifacts.
