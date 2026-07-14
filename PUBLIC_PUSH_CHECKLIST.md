<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Public Push Checklist

Version: `0.1.0` - Initial Public Research Release

This is a human approval gate. Local preparation does not authorize a push,
visibility change, tag, release, package upload, deployment, or announcement.
Record the reviewer, date, evidence, and disposition for every item. A checked
box without review evidence is not approval.

## Intellectual Property And Legal

- [ ] **IP and patent review:** an authorized reviewer has assessed Carter,
  SOS, EAS, SIS, CSC, the deterministic MCM, prompts, schemas, examples, and
  engineering packs for patent, trade-secret, employer, contract, and export
  issues.
- [ ] **Copyright ownership:** ownership of every released first-party file is
  confirmed, including migrated EAS modules, MCM, engineering packs, SIS
  excerpts, UI assets, and documentation.
- [ ] **Prior public grants:** the BSD-3-Clause documentation repositories and
  the AGPL release/migration language have been reviewed; no prior grant is
  described as withdrawn.
- [ ] **Third-party license review:** `THIRD_PARTY_NOTICES.md` and
  `LICENSE_COMPATIBILITY_REPORT.md` have been checked against exact release
  artifacts, upstream license texts, notices, and the complete transitive
  inventory. This review is performed by a qualified human, not inferred from
  package metadata alone.
- [ ] **Excluded assets:** `EXCLUSIONS.md` has been reviewed and no excluded
  third-party, unclear-ownership, private, or generated asset has entered the
  release.
- [ ] **AGPL notices:** the official unmodified AGPLv3 text, SPDX identifiers,
  copyright notices, contribution terms, network-source obligations, and
  package metadata are correct.
- [ ] **Trademark review:** `TRADEMARKS.md` is approved and makes no
  unsupported registration claim.

## Security And Privacy

- [ ] **Credential response:** every token visible in excluded legacy
  screenshots has been revoked or its expiry confirmed, and the histories of
  older public documentation repositories have been audited.
- [ ] **Secret scan:** `detect-secrets`, credential-signature searches, manual
  review, and a scan of every commit in the proposed public history are rerun
  after the final commit; findings and tool versions match
  `SECURITY_RELEASE_AUDIT.md`.
- [ ] **Privacy review:** no private memory, conversation, OpRep, account,
  email list, job payload, recording, image, voice identifier, database,
  Chroma store, log, or personal identifier is present in files or history.
- [ ] **Threat model:** authentication, CSRF, session isolation, SSE ownership,
  provider boundaries, sensory activation, retention, rate limits, and
  deployment assumptions in `docs/THREAT_MODEL.md` have been reviewed.
- [ ] **Dependency security:** the exact release environment passes
  `pip-audit`; ChromaDB remains absent while `CVE-2026-45829` has no approved
  fixed release.
- [ ] **Security contact:** the placeholder in `SECURITY.md` has been replaced
  with an approved private reporting channel before public visibility.

## Functionality And Evidence

- [ ] **Test results:** the reported collected, passed, failed, skipped, and
  coverage values are reproduced on supported Python versions; no standard
  test performs a paid or external API call.
- [ ] **Evidence reproduction:** `python -m examples.evidence.run_case --check`
  passes from the final commit and every checked-in evidence hash is verified.
- [ ] **Mock demonstration:** the default demonstration is run from a clean
  install with no credentials and is visibly labeled as deterministic mock
  behavior, not a language model.
- [ ] **Optional providers:** Ollama and any cloud/provider mode intended for
  the release are tested only with approved opt-in credentials/data, and
  unavailable dependencies fail cleanly.
- [ ] **Engineering review boundary:** EAS advisories, failed constraints,
  governance status, SIS hypotheses, and all professional-review warnings are
  accurate and prominent.
- [ ] **CSC privacy behavior:** microphone and camera are off by default,
  explicit activation and persistent active indicators work, browser-close
  cleanup is best effort, and cloud transfers are disclosed before use.
- [ ] **Package artifacts:** sdist and wheel build cleanly; installed-wheel
  health, license, evidence, static/template, and engineering-pack checks pass.

## Repository And Publication

- [ ] **Source-code link:** every interactive interface links to
  `https://github.com/mdlewis365/carter-synthetic-os` and exposes copyright,
  `AGPL-3.0-only`, and no-warranty notices.
- [ ] **Final diff:** an authorized reviewer has inspected `git diff`, the
  complete file list, executable bits, generated evidence, and every local
  commit; no unrelated or private file is staged.
- [ ] **Independent history:** the repository contains no private `.git`
  object, private commit, remote, tag, submodule, or copied Git metadata.
- [ ] **Release blockers:** every item in `RELEASE_BLOCKERS.md` is resolved or
  explicitly accepted by an authorized release owner with written rationale.
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
- [ ] **Older repositories:** archival or redirection of the documentation-only
  repositories is considered only after the canonical repository is public,
  verified, and linked; history is not rewritten merely to redirect it.

## Approval Record

| Role | Reviewer | Date | Evidence / decision |
| --- | --- | --- | --- |
| Release owner |  |  |  |
| Security/privacy reviewer |  |  |  |
| IP/license reviewer |  |  |  |
| Engineering-domain reviewer |  |  |  |

Publication authorization: **NOT GRANTED by this checklist in its current
unchecked state.**
