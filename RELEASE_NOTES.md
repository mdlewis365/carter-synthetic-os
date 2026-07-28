<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Release Notes Draft: 0.1.0

## Initial Public Research Release

Carter Synthetic OS `0.1.0` is the first proposed public implementation release
of Carter, the flagship implementation of Synthetic OS, in one monorepository.
EAS and SIS operate as functional systems within Carter, and CSC is the Carter
Sensory Console.

The release demonstrates a governed compound AI pipeline: probabilistic model planning/generation is separated from deterministic normalization, schema validation, computation, governance, and evidence generation. The basic mock demonstration runs without private data, a network connection, or a paid API. Local Ollama and cloud providers are optional.

## Included

- Carter session-scoped web workflow and streamed response boundary.
- SOS orchestration, memory contracts, governance, SAL, tool/provider boundaries, and redacted operational metadata.
- EAS two-stage planning/advisory workflow with MCM, units/constraints, EDR, engineering packs, and review gating.
- SIS structured invention modes, evaluator/feasibility interfaces, and governed hypothesis output.
- CSC explicit media controls, session-isolated transcript handling, optional interpretation/transcription/TTS, and local-only camera preview.
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

## Before Publication

These notes are a draft. No tag, GitHub release, visibility change, or remote push is authorized until the public push checklist, exact test/evidence results, dependency/license review, IP/patent review, and privacy/security audits receive human approval.
