<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Limitations

Carter Synthetic OS `0.1.0` is an initial public research release. Its implementation is real and runnable, but its scope is deliberately bounded.

## Platform

- Carter is a governed compound AI expert system and research platform, not AGI, unrestricted autonomy, consciousness, or sentience.
- The local Flask host is not a production multi-tenant identity or deployment platform.
- Mock mode demonstrates control flow with deterministic fixtures; it is not a language model and does not demonstrate model quality.
- Model output can be false, biased, inconsistent, incomplete, or unsafe.
- Optional provider behavior and availability can change independently of this repository.

## SOS And Memory

- DIM and SAL are new bounded public interfaces; no active standalone private implementation was available to migrate.
- SQLite is opt-in and is not presented as production data infrastructure. Chroma adapter source is included, but its affected dependency line is blocked and not installed.
- Retrieved memory is untrusted context, not verified fact.
- The repository ships no private memory, conversation store, knowledge base, model weights, or production OpRep.
- Governance and structured context reduce but do not eliminate prompt injection.

## EAS

- EAS is decision-support software and does not replace licensed engineering judgment, code review, safety analysis, field validation, or professional approval.
- Supported MCM calculations are only as valid as the inputs, equations, unit assumptions, boundary conditions, and criteria.
- Engineering packs are guidance context, not comprehensive codes or standards.
- No general production validation, regulatory qualification, or cross-discipline accuracy claim is made.

## SIS

- Generated concepts are hypotheses/candidates, not established inventions or discoveries.
- SIS does not establish novelty, patentability, freedom to operate, feasibility, safety, commercial value, or experimental validity.
- The release includes no patent-search engine or cleared private vector-template corpus.
- Evaluator and MCM coordination is a new `0.1.0` public integration and has limited validation history.

## CSC

- Wake-name detection is text classification, not speaker recognition, consent, or authentication.
- Transcription and interpretation can be wrong.
- Microphone and camera are disabled by default. Durable sensory retention is unavailable; in-process transcript state uses explicit clear and idle expiry.
- Camera support is limited to explicit local browser preview. There is no server-side camera interpretation in `0.1.0`.
- Cloud transcription/TTS transfers data to the selected provider and is subject to that provider's terms and controls.
- CSC is not a surveillance, medical, accessibility-certification, emergency, or safety-monitoring product.

## Security And Privacy

- A malicious host administrator can access process memory and environment credentials.
- The release has not been represented as independently penetration-tested.
- Enabling persistence, remote providers, uploads, or network exposure changes the threat model.
- Ephemeral deletion is not a cryptographic erasure guarantee.
- Dependency and model-license conclusions require continued human review.

## Current Private Implementation Comparison

- The current private Prompt Governance Module expresses named model-facing
  governance responsibilities through prompt construction. Those
  responsibilities are distinct from host authentication/authorization and
  separately implemented deterministic Python enforcement.
- The private host may supply the account email associated with its
  authenticated session as contextual identity metadata, not independent
  identity or authority. Session binding and account-context isolation require
  further hardening and testing.
- The private CSC has no camera implementation. AAM priority triage, SAL
  semantic adjudication, candidate queueing, and automatic response/TTS
  integration are still marked pending; CSC interpretation is not automatically
  submitted to Carter or PGM.
- Public mock-mode, provider, persistence, and orchestration behavior belongs to
  this research/reference implementation and is not behaviorally identical to
  the full private host.

## Legal And Research

The software provides no legal, patent, export-control, privacy, security,
medical, or regulatory advice. The canonical source repository is public and
the release-owner publication decisions are recorded as resolved or accepted.
The research limitations above are not themselves blockers to that public
source repository. Formal `0.1.0` tagging and release require exact verification
of the eventual documentation-merge commit and rebuilt release artifacts,
followed by separate tag and GitHub release authorization. As of this
reconciliation, no `v0.1.0` tag or GitHub release had been created; this PR
creates or authorizes neither.
