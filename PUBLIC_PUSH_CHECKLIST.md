<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Public Push Checklist

Version: `0.1.0` - Initial Public Research Release

This began as the human gate for the initial push and visibility change. Those
steps are complete: the canonical source repository is public. This tracked
document preserves the pre-tag source snapshot and the human procedure for a
version tag, GitHub release, package upload, deployment, or announcement. A
checked box without review evidence is not approval for a later action.

The 2026-07-25 technical checks, 2026-07-27 private-reference reconciliation,
and exact verification of release-candidate commit `7acd4c4` are summarized in
`PUBLIC_RELEASE_REPORT.md` and `SECURITY_RELEASE_AUDIT.md`. Michael D. Lewis
recorded the release-owner decisions below on July 28, 2026. The
pre-reconciliation public baseline, verified on July 29, 2026, was
`396deb6d5f2b86bde46c6d6ac4e18f448f4ed941`, with 193 tracked files.
`docs/PGM.md` is committed and public. The initial private push, public
visibility change, and subsequent CI verification are complete.
Documentation reconciliation PR #5 was merged normally as commit
`3e294c7905831dbdf3d1a4e174251f32c341b460`, with tree
`3dc04c43cc76964f5ed061b97c52c3d71a718842`; it changed only 14 Markdown
files and did not create or authorize a tag or GitHub release.

The pre-tag source snapshot verified on July 31, 2026, was
`e080532dca47282e12711caa8fe92b27a8ff4afb`, with tree
`2c10515e88ae094c38515e6e0d9b5ac717401f78` and 194 tracked files. Its 231
offline tests, branch-aware coverage, Windows installed-wheel smoke, scans,
builds, CodeQL analyses, and GitHub checks passed. This dated snapshot is
evidence, not a prediction of the commit ultimately selected for the tag.

## Intellectual Property And Legal

- [x] **IP and patent decision:** the release owner knowingly chose public
  disclosure without obtaining patent review first and accepts its possible
  effect on patent options. No patentability conclusion is stated.
- [x] **Copyright ownership:** ownership of every released first-party file is
  confirmed, including migrated EAS modules, MCM, engineering packs, SIS
  excerpts, UI assets, and documentation.
- [x] **Prior public grants:** the BSD-3-Clause documentation repositories and
  the AGPL release/migration language have been reviewed; no prior grant is
  described as withdrawn.
- [x] **Third-party license decision:** the release owner accepts the documented
  technical review in `THIRD_PARTY_NOTICES.md` and
  `LICENSE_COMPATIBILITY_REPORT.md` for this release. This is not a legal
  opinion; no dependency source is bundled or vendored, and future resolutions
  and rebuilt artifacts require re-audit.
- [x] **Excluded assets:** `EXCLUSIONS.md` has been reviewed and no excluded
  third-party, unclear-ownership, private, or generated asset has entered the
  release.
- [x] **AGPL notices:** the official unmodified AGPLv3 text, SPDX identifiers,
  copyright notices, contribution terms, network-source obligations, and
  package metadata are correct.
- [x] **Trademark review:** `TRADEMARKS.md` is approved and makes no
  unsupported registration claim.

## Security And Privacy

- [x] **Credential response:** committed lifecycle evidence established that
  the three excluded legacy screenshots contained two random, process-local,
  in-memory session bearer tokens with 24-hour expiration. The screenshots
  entered the legacy repositories on June 25, 2026, so the sessions expired by
  June 26, 2026 at the latest under that implementation; a restart also
  invalidated them. No role password or evidence of misuse was found. Screenshot
  replacement/removal remains repository hygiene.
- [x] **Secret scan:** baseline-aware detect-secrets,
  credential-signature/path/artifact searches, public-history review, and
  GitHub secret scanning passed for the July 29 pre-reconciliation baseline; at
  that verification point, open secret-scanning alerts were zero. Repeat these
  checks for the exact commit selected as the version-tag target and for
  artifacts rebuilt from it.
- [x] **Privacy review:** no private memory, conversation, OpRep, account,
  email list, job payload, recording, image, voice identifier, database,
  Chroma store, log, or unapproved personal identifier is present in files or
  history. The release owner intentionally approves publication of his name,
  business identity, and Git author email.
- [x] **Threat model:** authentication, CSRF, session isolation, SSE ownership,
  provider boundaries, sensory activation, retention, rate limits, and
  deployment assumptions in `docs/THREAT_MODEL.md` have been reviewed.
- [x] **PGM boundary disclosure:** the release owner has reviewed the public
  PGM, account-context, emergency-claim, tool-action, privacy, security, and
  threat-model wording and confirmed that it is accurate without exposing
  operative prompt language or unnecessary private authentication/session
  mechanics.
- [x] **Dependency security:** strict project dependency auditing passed for
  the July 29 pre-reconciliation baseline; at that verification point, open
  Dependabot vulnerability alerts were zero. ChromaDB remains absent while its
  affected dependency line has no approved fixed release. Re-audit future
  resolutions and rebuilt artifacts.
- [x] **Security contact:** `SECURITY.md` contains the tested, monitored private
  reporting address approved by the release owner.

## Functionality And Evidence

- [x] **Test results:** the July 29 pre-reconciliation baseline passed 226
  offline tests with 35% branch-aware overall coverage, 20% MCM coverage, and
  83% web-boundary coverage. Supported-version GitHub jobs passed and no
  standard test performed a paid or external API call.
- [x] **Evidence reproduction:**
  `python -m examples.evidence.run_case --check` passes and checked-in evidence
  is self-consistent and semantically reproducible.
- [x] **Mock demonstration:** clean-install and installed-wheel smoke checks
  exercise the no-credential mock/health path, which remains visibly
  deterministic mock behavior rather than a language model.
- [x] **Optional providers:** unexecuted live-provider and hardware checks are
  accepted as disclosed, opt-in research limitations; unavailable dependencies
  fail cleanly and no live-provider certification is claimed.
- [x] **Engineering review boundary:** EAS advisories, failed constraints,
  governance status, SIS hypotheses, and all professional-review warnings are
  accurate and prominent.
- [x] **CSC privacy behavior:** microphone and camera are off by default,
  explicit activation and persistent active indicators work, browser-close
  cleanup is best effort, and cloud transfers are disclosed before use.
- [x] **Package artifacts:** source and wheel builds, wheel inspection, and
  installed-wheel health/license/evidence/static/template/engineering-pack
  smoke checks passed for the recorded baselines. Rebuild and reverify artifacts
  from the exact commit selected as the version-tag target.

## Repository And Publication

- [x] **Source-code link:** every interactive interface links to
  `https://github.com/mdlewis365/carter-synthetic-os` and exposes copyright,
  `AGPL-3.0-only`, and no-warranty notices.
- [ ] **Final documentation/release diff:** an authorized reviewer inspects the
  exact commit selected as the version-tag target, executable bits, rebuilt
  artifacts, and final pre-tag diff; no unrelated or private file enters the
  release.
- [x] **Independent history:** the repository contains no private `.git`
  object, private commit, submodule, or copied private Git metadata. Its
  configured canonical GitHub remote is intentional.
- [x] **Release-owner gates:** B-01 through B-07 in `RELEASE_BLOCKERS.md` are
  resolved or explicitly accepted by Michael D. Lewis with written rationale.
  B-08 is satisfied for the recorded earlier baselines and applies anew to every
  commit selected as a version-tag target and to artifacts rebuilt from it.
- [x] **Repository visibility:** the canonical repository under
  `mdlewis365/carter-synthetic-os` is public and its default branch is `main`.
- [x] **First public commit:** the reviewed source history is on public `main`;
  branch protection and checked-in CI/security workflows are active.
- [x] **First push:** the authorized initial private push, later visibility
  change, and public-state verification were completed.
- [ ] **Release-tag procedure:** after the exact tag target and rebuilt
  artifacts are verified and separately authorized, a human creates the
  approved `v0.1.0` tag and GitHub release.
- [x] **Older repositories:** replacement/removal of the legacy credential-bearing
  screenshots is recorded as a separate repository-hygiene task. Archival or
  redirection of the documentation-only
  repositories remains a separate decision now that the canonical repository
  is public, verified, and linked; history is not rewritten merely to redirect
  it.

## Approval Record

| Role | Reviewer | Date | Evidence / decision |
| --- | --- | --- | --- |
| Release owner | Michael D. Lewis | 2026-07-28 | Approved B-01 through B-07, the public PGM, disclosed limitations, and exact verification evidence for `7acd4c4`; chose public disclosure without prior patent review. |
| Security/privacy reviewer | Michael D. Lewis | 2026-07-28 | Approved privacy/exclusions, public identity, token-lifecycle disposition, and tested security/privacy contacts. |
| IP/license decision | Michael D. Lewis | 2026-07-28 | Authorized `AGPL-3.0-only` distribution and accepted the documented technical dependency-license evidence; not a legal opinion. |
| Engineering-domain decision | Michael D. Lewis | 2026-07-28 | Approved the 18-pack provenance record and accepted the disclosed lack of independent professional validation. |
| Public source verification | Automated and human-directed review | 2026-07-29 | Verified the pre-reconciliation public baseline at `396deb6d5f2b86bde46c6d6ac4e18f448f4ed941`; PRs #3 and #4 had merged normally; CodeQL alerts #1 through #7 were fixed without dismissal; open CodeQL, secret-scanning, and Dependabot vulnerability alert counts were zero at that verification point. |

Publication authorization is **not granted by this tracked checklist alone.**
For a release, verify the exact `v0.1.0` tag target and artifacts rebuilt from
it, then obtain the applicable authorization. Completion of exact-commit
verification, tag creation, artifact upload, and GitHub release publication is
recorded externally in the Git tag, final verification report, and GitHub
release metadata rather than self-referentially in the commit being verified.
