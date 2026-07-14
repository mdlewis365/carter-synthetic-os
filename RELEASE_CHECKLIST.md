<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Release Preparation Checklist

This checklist covers local preparation for `0.1.0`. `PUBLIC_PUSH_CHECKLIST.md` contains the mandatory human authorization gates for publication. Checking an item here does not authorize a push, tag, release, or visibility change.

## Repository

- [ ] Work is on `release/carter-agpl-public` in the independent public repository.
- [ ] No private `.git` directory or private history is present.
- [ ] Private source and older documentation repositories remain unchanged.
- [ ] Version is `0.1.0` and release name is **Initial Public Research Release**.
- [ ] Final diff and local logical commits have been reviewed.

## Implementation

- [ ] Carter, SOS, EAS, SIS, and CSC first-party implementation is present.
- [ ] Mock demonstration works without credentials/network/private data.
- [ ] Ollama unavailable behavior is explicit and cloud SDKs are optional/lazy.
- [ ] Retention, microphone, and camera are disabled by default.
- [ ] Every web interface shows copyright, AGPL, no-warranty, license, and canonical source notices.

## Security And Privacy

- [ ] Text, history, dependency, archive, and generated-artifact secret scans are clean or explained.
- [ ] Manual review covers images, audio, databases, logs, prompts, memories, and identity data.
- [ ] No real `.env`, credential, token, voice ID, account ID, user record, or private URL is present.
- [ ] Session ownership, route authorization, SSE, provider failure, and CSC isolation tests pass.
- [ ] Approved private security/privacy/moderation contacts replace or resolve placeholders.

## Legal And Provenance

- [ ] Complete unmodified AGPLv3 text and `AGPL-3.0-only` identifiers are present.
- [ ] First-party copyright and contribution notices are reviewed.
- [ ] Engineering packs and SIS authorship/patent provenance receive human signoff.
- [ ] Direct dependency licenses and required notices receive human review.
- [ ] No uncleared third-party source, assets, models, datasets, fonts, media, or standards text is included.

## Verification

- [ ] Fresh-environment install and package build succeed.
- [ ] Complete non-network test results and coverage are recorded exactly.
- [ ] Evidence artifacts regenerate with `python -m examples.evidence.run_case` and hashes match.
- [ ] Lint, format, type/security checks, dependency audit, and secret scan are recorded.
- [ ] Documentation commands, links, configuration, diagrams, and limitations match code.

## Stop Point

- [ ] No remote push was performed.
- [ ] No public tag or release was created.
- [ ] Repository visibility was not changed.
- [ ] Human reviewers received the audit reports and `PUBLIC_PUSH_CHECKLIST.md`.
