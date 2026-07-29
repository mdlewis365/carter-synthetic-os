<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Public Push Checklist

Version: `0.1.0` - Initial Public Research Release

This is a human approval gate. Local preparation does not authorize a push,
visibility change, tag, release, package upload, deployment, or announcement.
Record the reviewer, date, evidence, and disposition for every item. A checked
box without review evidence is not approval.

The 2026-07-25 technical checks, 2026-07-27 private-reference reconciliation,
and exact verification of release-candidate commit `7acd4c4` are summarized in
`PUBLIC_RELEASE_REPORT.md` and `SECURITY_RELEASE_AUDIT.md`. Michael D. Lewis
recorded the release-owner decisions below on July 28, 2026. The
documentation-only commit carrying this record still requires exact
post-commit verification and separate remote/push authorization.

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
- [ ] **Secret scan:** `detect-secrets`, credential-signature searches, manual
  review, and a scan of every commit in the proposed public history are rerun
  after the final commit; findings and tool versions match
  `SECURITY_RELEASE_AUDIT.md`.
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
- [ ] **Dependency security:** the exact release environment passes
  `pip-audit`; ChromaDB remains absent while `CVE-2026-45829` has no approved
  fixed release.
- [x] **Security contact:** `SECURITY.md` contains the tested, monitored private
  reporting address approved by the release owner.

## Functionality And Evidence

- [ ] **Test results:** the reported collected, passed, failed, skipped, and
  coverage values are reproduced on supported Python versions; no standard
  test performs a paid or external API call.
- [ ] **Evidence reproduction:** `python -m examples.evidence.run_case --check`
  passes from the final commit and every checked-in evidence hash is verified.
- [ ] **Mock demonstration:** the default demonstration is run from a clean
  install with no credentials and is visibly labeled as deterministic mock
  behavior, not a language model.
- [x] **Optional providers:** unexecuted live-provider and hardware checks are
  accepted as disclosed, opt-in research limitations; unavailable dependencies
  fail cleanly and no live-provider certification is claimed.
- [x] **Engineering review boundary:** EAS advisories, failed constraints,
  governance status, SIS hypotheses, and all professional-review warnings are
  accurate and prominent.
- [x] **CSC privacy behavior:** microphone and camera are off by default,
  explicit activation and persistent active indicators work, browser-close
  cleanup is best effort, and cloud transfers are disclosed before use.
- [ ] **Package artifacts:** sdist and wheel build cleanly; installed-wheel
  health, license, evidence, static/template, and engineering-pack checks pass.

## Repository And Publication

- [x] **Source-code link:** every interactive interface links to
  `https://github.com/mdlewis365/carter-synthetic-os` and exposes copyright,
  `AGPL-3.0-only`, and no-warranty notices.
- [ ] **Final diff:** an authorized reviewer has inspected `git diff`, the
  complete file list, executable bits, generated evidence, and every local
  commit; no unrelated or private file is staged.
- [x] **Independent history:** the repository contains no private `.git`
  object, private commit, remote, tag, submodule, or copied Git metadata.
- [x] **Release-owner gates:** B-01 through B-07 in `RELEASE_BLOCKERS.md` are
  resolved or explicitly accepted by Michael D. Lewis with written rationale.
  B-08 remains the exact post-commit verification gate for the
  documentation-only record-carrying commit.
- [ ] **Repository visibility:** the canonical GitHub repository exists under
  the intended owner and its visibility change is approved only after all
  preceding gates pass.
- [ ] **First public commit:** the exact reviewed local commit IDs and branch
  are selected for the first push; branch protection and required checks are
  configured before accepting contributions.
- [ ] **First push:** a human performs and verifies the push. This local
  preparation process does not push.
- [ ] **Release tag:** only after the public repository and CI are verified, a
  human creates and signs/annotates the approved `v0.1.0` tag and release.
- [x] **Older repositories:** replacement/removal of the legacy credential-bearing
  screenshots is recorded as a separate repository-hygiene task. Archival or
  redirection of the documentation-only
  repositories is considered only after the canonical repository is public,
  verified, and linked; history is not rewritten merely to redirect it.

## Approval Record

| Role | Reviewer | Date | Evidence / decision |
| --- | --- | --- | --- |
| Release owner | Michael D. Lewis | 2026-07-28 | Approved B-01 through B-07, the public PGM, disclosed limitations, and exact verification evidence for `7acd4c4`; chose public disclosure without prior patent review. |
| Security/privacy reviewer | Michael D. Lewis | 2026-07-28 | Approved privacy/exclusions, public identity, token-lifecycle disposition, and tested security/privacy contacts. |
| IP/license decision | Michael D. Lewis | 2026-07-28 | Authorized `AGPL-3.0-only` distribution and accepted the documented technical dependency-license evidence; not a legal opinion. |
| Engineering-domain decision | Michael D. Lewis | 2026-07-28 | Approved the 18-pack provenance record and accepted the disclosed lack of independent professional validation. |

Publication authorization: **NOT GRANTED by this checklist alone.** Exact
verification of the documentation-only record-carrying commit and separate
authorization to configure a remote or push remain required.
