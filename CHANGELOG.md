<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Changelog

All notable public changes will be recorded here. The project follows semantic versioning where practical, while `0.x` releases may change public interfaces as research boundaries mature.

## [Unreleased]

## [0.1.0] - 2026-07-31

**Initial Public Research Release**

### Changed

- Made the default UTC temporal anchor self-contained with Python's built-in
  UTC timezone and added an isolated Windows installed-wheel smoke check that
  runs the complete public mock experience without `tzdata` or system IANA
  timezone data.
- Published the canonical source repository at
  `https://github.com/mdlewis365/carter-synthetic-os`. The pre-reconciliation
  public baseline, verified on July 29, 2026, was
  `396deb6d5f2b86bde46c6d6ac4e18f448f4ed941`. At that point, version
  `0.1.0` was unreleased and no `v0.1.0` tag or GitHub release had been
  created.
- Merged documentation reconciliation PR #5 normally as commit
  `3e294c7905831dbdf3d1a4e174251f32c341b460`, with tree
  `3dc04c43cc76964f5ed061b97c52c3d71a718842`. It changed only 14 Markdown
  files and did not create or authorize a tag or GitHub release.
- Merged security remediation PRs #3 and #4 with normal merge commits. CodeQL
  automatically marked alerts #1 through #7 fixed without dismissal. At the
  July 29 baseline verification, open CodeQL, secret-scanning, and Dependabot
  vulnerability alert counts were zero.
- The July 29 baseline passed 226 offline tests with 35% branch-aware overall
  coverage, 20% MCM coverage, and 83% web-boundary coverage.
- Reconciled maintained documentation through private commit `df0230b` without
  copying private prompt or account data.
- Documented the public-safe architectural boundary for the revised private
  Prime Directives and Emergency Claims and Tool-Action Governance without
  reproducing operative prompt language.
- Documented removal of SOSP from current PGM, the implemented Prompt
  Governance Module responsibilities, and the host-supplied
  authenticated-session account-email context/privacy boundary.
- Distinguished host/deterministic controls from model-facing PGM governance
  and planned or experimental CSC behavior, and corrected public SAL/MCM
  terminology.
- Minimized public response metadata by replacing configured model identifiers
  with configuration-presence booleans and removing the session-derived TTS
  header.
- Added an explicit secure-cookie configuration switch and documented the
  public runtime's lack of production user authentication.
- Renamed the EAS deterministic completion state from the misleading
  `computed_certified` label to `computed_criteria_passed`.
- Added tests for metadata minimization, secure-cookie propagation, and the
  corrected EAS gate status.

### Added

- Carter governed conversational orchestration, provider selection, session ownership, and Server-Sent Events interface.
- Synthetic OS normalization, context assembly, CRM/AMS memory contracts, new public DIM and SAL boundaries, governance, metadata logging, and optional storage/provider adapters.
- Deterministic mock provider, optional local Ollama provider, and optional OpenAI, Anthropic, and Google provider boundaries.
- Engineering Assistance System two-stage workflow, engineering packs, schema validation, MCM calculation, EDR, governance, and mandatory human-review status.
- Synthetic Ideation System modes, structured scientist input, evaluators, feasibility/MCM boundary, and governed hypothesis output.
- Carter Sensory Console session isolation, explicit audio capture, WAV/transcription boundary, wake-name/role classification, rolling transcript, optional local interpretation and TTS, and local camera preview boundary.
- Synthetic reproducible evidence case, non-network tests, security/quality automation, community files, and architecture/operator documentation.
- GNU Affero General Public License v3.0 only licensing and interactive source/legal notices.

### Security And Privacy

- No private repository history, active credentials, private memories, conversations, databases, vector stores, logs, recordings, cloned voice assets, or production authentication data are included.
- Loopback binding, debug off, persistence off, sensory retention off, and mock mode are defaults.
- Optional SDKs load lazily and provider failures remain explicit.

### Known Limits

- DIM and SAL are bounded new public interfaces rather than migrated active private modules.
- Camera support is local preview only.
- EAS requires independent professional review; SIS candidates require technical, patent, prior-art, safety, and experimental review.
- Release-owner decisions B-01 through B-07 are resolved. Release policy
  requires the exact commit selected for a version tag and artifacts rebuilt
  from that commit to pass the complete verification suite before separate tag
  and GitHub release authorization.

[Unreleased]: https://github.com/mdlewis365/carter-synthetic-os/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mdlewis365/carter-synthetic-os/releases/tag/v0.1.0
