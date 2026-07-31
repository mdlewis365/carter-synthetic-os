<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Release Preparation Checklist

This checklist began as local preparation for `0.1.0` and now records the
verified public-source state. `PUBLIC_PUSH_CHECKLIST.md` contains the remaining
human authorization gates for the formal tag and GitHub release. Checking an
item here does not authorize a merge, tag, or release.

Automated working-tree status was updated on 2026-07-25, the committed private
reference was reconciled and the full public offline suite rerun on 2026-07-27,
and release-owner decisions B-01 through B-07 were recorded on 2026-07-28.
The canonical repository is public. Its pre-reconciliation baseline
(`396deb6d5f2b86bde46c6d6ac4e18f448f4ed941`) passed CI and exact-tree
verification on July 29, 2026. Documentation reconciliation PR #5 was merged
normally as commit `3e294c7905831dbdf3d1a4e174251f32c341b460`, with tree
`3dc04c43cc76964f5ed061b97c52c3d71a718842`; it changed only 14 Markdown
files and did not create or authorize a tag or GitHub release. The exact commit
selected for a version tag and artifacts rebuilt from it remain subject to the
complete verification suite before tag and release authorization.

## Repository

- [x] The independent canonical repository is public, with `main` as its
  default branch. The maintained `v0.1.0` candidate tree including the PR #7
  Windows/UTC correction contains 194 tracked files.
- [x] No private `.git` directory or private history is present.
- [x] Private source and older documentation repositories remain unchanged.
- [x] Version is `0.1.0` and release name is **Initial Public Research Release**.
- [x] Documentation reconciliation PR #5 was reviewed and merged normally,
  changing only 14 Markdown files.
- [ ] The exact commit selected as the version-tag target, rebuilt artifacts,
  and final pre-tag diff have received complete verification and separate
  review.

## Implementation

- [x] Carter, SOS, EAS, SIS, and CSC first-party implementation is present.
- [x] Mock demonstration works without credentials/network/private data.
- [x] Ollama unavailable behavior is explicit and cloud SDKs are optional/lazy.
- [x] Retention, microphone, and camera are disabled by default.
- [x] Every web interface shows copyright, AGPL, no-warranty, license, and designated source notices.

## Security And Privacy

- [x] Text, history, dependency, archive, and generated-artifact secret scans
  were clean or explained for the July 29 baseline; open GitHub
  secret-scanning alerts were zero at that verification point.
- [x] Manual review covers images, audio, databases, logs, prompts, memories, and identity data.
- [x] No real `.env`, credential, token, voice ID, account ID, user record, or private URL is present.
- [x] Session ownership, route authorization, SSE, provider failure, and CSC isolation tests pass.
- [x] Approved security, privacy, trademark/branding, and private moderation contacts replace all publication placeholders.

## Legal And Provenance

- [x] Complete unmodified AGPLv3 text and `AGPL-3.0-only` identifiers are present.
- [x] First-party copyright and contribution notices are reviewed.
- [x] Engineering packs and SIS authorship/patent provenance receive release-owner signoff.
- [x] The release owner accepts the documented technical dependency-license review, without treating it as a legal opinion.
- [x] No uncleared third-party source, assets, models, datasets, fonts, media, or standards text is included to the best of the release owner's knowledge.

## Verification

- [x] Fresh-environment install, source build, wheel build, inspection, and
  installed-wheel smoke succeeded for the July 29 pre-reconciliation baseline.
- [x] Complete non-network test results and coverage are recorded exactly.
- [x] Evidence artifacts reproduce with `python -m examples.evidence.run_case --check` and hashes match.
- [x] Ruff lint/format, Bandit, CodeQL, dependency audit, and baseline-aware
  secret scanning are recorded and passed for the July 29 pre-reconciliation
  baseline.
- [x] Documentation commands, links, configuration, diagrams, and limitations match code.

## Stop Point

- [x] The initial private push, public visibility change, and public `main`
  verification were completed.
- [x] As of the July 29, 2026 reconciliation snapshot, no public tag or release
  had been created; PR #5 created or authorized neither.
- [x] Repository visibility is public and the default branch is `main`.
- [x] The release owner reviewed the audit reports and `PUBLIC_PUSH_CHECKLIST.md`.
