<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Release Preparation Checklist

This checklist covers local preparation for `0.1.0`. `PUBLIC_PUSH_CHECKLIST.md` contains the mandatory human authorization gates for publication. Checking an item here does not authorize a push, tag, release, or visibility change.

Automated working-tree status was updated on 2026-07-25, the committed private
reference was reconciled and the full public offline suite rerun on 2026-07-27,
and release-owner decisions B-01 through B-07 were recorded on 2026-07-28.
Items requiring the exact documentation-only record-carrying commit remain
unchecked until their results are recorded externally.

## Repository

- [x] Work is on `release/carter-agpl-public` in the independent public repository.
- [x] No private `.git` directory or private history is present.
- [x] Private source and older documentation repositories remain unchanged.
- [x] Version is `0.1.0` and release name is **Initial Public Research Release**.
- [ ] Final diff and local logical commits have been reviewed.

## Implementation

- [x] Carter, SOS, EAS, SIS, and CSC first-party implementation is present.
- [x] Mock demonstration works without credentials/network/private data.
- [x] Ollama unavailable behavior is explicit and cloud SDKs are optional/lazy.
- [x] Retention, microphone, and camera are disabled by default.
- [x] Every web interface shows copyright, AGPL, no-warranty, license, and designated source notices.

## Security And Privacy

- [ ] Text, history, dependency, archive, and generated-artifact secret scans are clean or explained.
- [x] Manual review covers images, audio, databases, logs, prompts, memories, and identity data.
- [x] No real `.env`, credential, token, voice ID, account ID, user record, or private URL is present.
- [x] Session ownership, route authorization, SSE, provider failure, and CSC isolation tests pass.
- [x] Approved security, privacy, and trademark/branding contacts replace all publication placeholders.

## Legal And Provenance

- [x] Complete unmodified AGPLv3 text and `AGPL-3.0-only` identifiers are present.
- [x] First-party copyright and contribution notices are reviewed.
- [x] Engineering packs and SIS authorship/patent provenance receive release-owner signoff.
- [x] The release owner accepts the documented technical dependency-license review, without treating it as a legal opinion.
- [x] No uncleared third-party source, assets, models, datasets, fonts, media, or standards text is included to the best of the release owner's knowledge.

## Verification

- [ ] Fresh-environment install and package build succeed.
- [x] Complete non-network test results and coverage are recorded exactly.
- [x] Evidence artifacts reproduce with `python -m examples.evidence.run_case --check` and hashes match.
- [ ] Lint, format, type/security checks, dependency audit, and secret scan are recorded.
- [x] Documentation commands, links, configuration, diagrams, and limitations match code.

## Stop Point

- [x] No remote push was performed.
- [x] No public tag or release was created.
- [x] Repository visibility was not changed.
- [x] The release owner reviewed the audit reports and `PUBLIC_PUSH_CHECKLIST.md`.
