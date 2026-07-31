<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Release Notes: 0.1.0

## Initial Public Research Release

Carter Synthetic OS `0.1.0` is the Initial Public Research Release of the
public Carter/Synthetic OS reference implementation. Carter is the flagship
implementation of Synthetic OS in this monorepository.
EAS and SIS operate as functional systems within Carter, and CSC is the Carter
Sensory Console.

The release demonstrates a governed compound AI pipeline: probabilistic model planning/generation is separated from deterministic normalization, schema validation, computation, governance, and evidence generation. The basic mock demonstration runs without private data, a network connection, or a paid API. Local Ollama and cloud providers are optional.

## Included

- Carter session-scoped web workflow and streamed response boundary.
- SOS orchestration, memory contracts, governance, SAL, tool/provider boundaries, and redacted operational metadata.
- EAS two-stage planning/advisory workflow with MCM, units/constraints, EDR, engineering packs, and review gating.
- SIS structured invention modes, evaluator/feasibility interfaces, and governed hypothesis output.
- CSC explicit media controls, session-isolated transcript handling, optional interpretation/transcription/TTS, and local-only camera preview.
- Self-contained default UTC anchors and a clean Windows installed-wheel smoke
  that exercises the complete public mock experience without `tzdata` or
  system IANA timezone data.
- Reproducible synthetic evidence, non-network tests, CI/security configuration, and substantive documentation.

## Important Boundaries

EAS is engineering decision-support software and every result requires qualified human review. SIS outputs are hypotheses/candidates requiring independent validation, prior-art and patent analysis, safety assessment, and experiment. CSC media features are disabled until explicit activation and do not retain sensory data by default.

The maintained Carter deployment is authentication-protected, and guided or
demonstration access may be available upon request. The public research runtime
does not contain that private authentication implementation: it provides
signed anonymous session ownership and CSRF controls, not verified real-world
identity, account isolation, or production authorization. HTTPS deployments
must enable the secure-cookie setting.

DIM and SAL are new bounded public `0.1.0` interfaces. No active private DIM/SAL subsystem was available to migrate. The private source also had no camera implementation; this release's camera boundary is browser-local preview only.

## Upgrade And Migration

This is the first installable public version, so no package upgrade path exists. Readers of the older documentation-only repositories should use [MIGRATION.md](MIGRATION.md). Existing BSD-3-Clause grants for those historical versions remain effective.

## Publication And Verification Snapshot: July 29, 2026

The release-owner decisions for authorship/AGPL authority, patent-disclosure
timing, engineering-pack provenance, technical dependency licensing, legacy
session-token lifecycle, privacy/exclusions, and operational contacts were
recorded on July 28, 2026. The canonical repository is public at
`https://github.com/mdlewis365/carter-synthetic-os`. Its pre-reconciliation
public baseline, verified on July 29, 2026, was
`396deb6d5f2b86bde46c6d6ac4e18f448f4ed941`, with 193 tracked files.
`docs/PGM.md` is committed and public.

Security remediation PRs #3 and #4 were merged normally. CodeQL automatically
marked alerts #1 through #7 fixed without dismissal. At the July 29 baseline
verification, open CodeQL, secret-scanning, and Dependabot vulnerability alert
counts were zero. That baseline passed 226 tests with 35% branch-aware overall
coverage, 20% MCM coverage, and 83% web-boundary coverage. Ruff, Bandit,
baseline-aware detect-secrets, dependency auditing, builds, installed-wheel
smoke, evidence reproduction, and GitHub workflows passed.

As of the July 29, 2026 reconciliation snapshot, no `v0.1.0` tag or GitHub
release had been created. Documentation reconciliation PR #5 was subsequently
merged normally as commit `3e294c7905831dbdf3d1a4e174251f32c341b460`,
with tree `3dc04c43cc76964f5ed061b97c52c3d71a718842`; it changed only
14 Markdown files and created or authorized neither a tag nor a GitHub release.
Release policy requires the exact commit selected for a version tag and
artifacts rebuilt from it to pass the complete verification suite before
separate tag and GitHub release authorization.
