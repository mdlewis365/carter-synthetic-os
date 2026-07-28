<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Release Preparation Checklist

This checklist covers local preparation for `0.1.0`. `PUBLIC_PUSH_CHECKLIST.md` contains the mandatory human authorization gates for publication. Checking an item here does not authorize a push, tag, release, or visibility change.

Automated working-tree status was updated on 2026-07-25, and the committed
private reference was reconciled and the full public offline suite rerun on
2026-07-27. Items requiring human judgment, an exact committed artifact, or an
approved external contact remain unchecked.

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
- [ ] Manual review covers images, audio, databases, logs, prompts, memories, and identity data.
- [ ] No real `.env`, credential, token, voice ID, account ID, user record, or private URL is present.
- [x] Session ownership, route authorization, SSE, provider failure, and CSC isolation tests pass.
- [ ] Approved private security/privacy/moderation contacts replace or resolve placeholders.

## Legal And Provenance

- [x] Complete unmodified AGPLv3 text and `AGPL-3.0-only` identifiers are present.
- [ ] First-party copyright and contribution notices are reviewed.
- [ ] Engineering packs and SIS authorship/patent provenance receive human signoff.
- [ ] Direct dependency licenses and required notices receive human review.
- [ ] No uncleared third-party source, assets, models, datasets, fonts, media, or standards text is included.

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
- [ ] Human reviewers received the audit reports and `PUBLIC_PUSH_CHECKLIST.md`.
