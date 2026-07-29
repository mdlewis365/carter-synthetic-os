<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Release Blockers

Release: `0.1.0` (Initial Public Research Release)

Status date: 2026-07-28

**Publication status: release-owner decisions for B-01 through B-07 are
recorded.** The documentation-only commit carrying this record must receive
exact post-commit verification before a separate human authorization may
configure a remote or push. This document does not authorize a GitHub push,
visibility change, tag, or public release.

This document distinguishes publication gates from optional capabilities that
are deliberately disabled or have not received external validation. It does not
claim legal, security, scientific, or professional-engineering approval.

Before creation of the release-candidate commit, staged-candidate verification
was completed for 40 changed paths in a 193-file indexed tree. Its complete
cached diff was inspected, the baseline-aware `detect-secrets-hook` passed
without mutating `.secrets.baseline`, and all other staged technical checks
passed. Exact-commit and release-artifact verification was required after
commit creation, with the results recorded without modifying the exact commit
being verified. At the time this staged-candidate record was prepared, B-01
through B-08 and all applicable human publication gates remained open.

Commit `7acd4c4cbeb248004e05ab0de7150bbfae7e7167` was subsequently verified as
an exact 193-file release-candidate tree. Its tests, scans, evidence, build,
wheel, engineering-pack, and public/private PGM boundary checks passed. Michael
D. Lewis accepted that exact-commit evidence on July 28, 2026. The
documentation-only successor that contains this approval record must be
verified after creation, with its SHA and results recorded externally rather
than inserted into the commit itself.

## Publication-Gate Disposition

| ID | July 28, 2026 disposition | Preserved qualification | Status |
| --- | --- | --- | --- |
| B-01 | Michael D. Lewis, the sole human developer and release owner, recorded his ownership and distribution-authority decision. To the best of his knowledge, no employer, client, collaborator, contractor, or other person holds rights restricting the release, and no unauthorized third-party material is included. He authorizes `AGPL-3.0-only` distribution. | AI systems were development tools under his direction, selection, integration, modification, testing, organization, and approval. No claim is made that every AI-generated element independently qualifies for copyright protection. | Owner gate resolved. |
| B-02 | Michael knowingly chose to proceed with public disclosure without obtaining patent review first and accepts the possible effect on patent options. | No statement is made that any material is or is not patentable. | Owner gate resolved. |
| B-03 | Michael recorded that all 18 engineering packs were produced through his AI-assisted development process, reviewed and approved by him, and were not knowingly copied or adapted from paid standards, proprietary manuals, employer/customer procedures, protected tables, controlled-source examples, or other unauthorized third-party material. | The packs remain research guidance, not standards or independent professional validation. | Owner gate resolved. |
| B-04 | Michael accepted the documented technical dependency-license review for this Initial Public Research Release. | This is owner acceptance of technical evidence, not a legal opinion. No dependency source is bundled or vendored in the wheel. Future resolutions and rebuilt artifacts must be re-audited. | Owner gate resolved. |
| B-05 | Offline source and lifecycle review established that the three legacy screenshots exposed two genuine random session bearer tokens. The in-memory, process-local sessions expired after 24 hours; the screenshots entered the legacy repositories on June 25, 2026, so under the committed implementation the sessions expired by June 26, 2026 at the latest. Any server restart also invalidated them. | No role password was exposed, and no evidence of unauthorized use was found; misuse is not claimed to have been mathematically impossible. Present validity is reasonably excluded by the documented expiration and in-memory lifecycle. Screenshot replacement/removal remains repository hygiene, not a blocker for this candidate. | Owner gate resolved. |
| B-06 | Tested, monitored security, privacy, and trademark/branding contacts were approved and placed in their respective policy files. | GitHub Private Vulnerability Reporting remains optional until separately enabled and tested. | Owner gate resolved. |
| B-07 | Michael approved `docs/PGM.md`, the privacy and exclusion findings, and intentional publication of his name, business identity, and Git author email. He also accepted the disclosed coverage, independent-validation, disabled-ChromaDB, and optional-integration limitations. | Automated scans do not replace future review of changed files or artifacts. No private prompt or private operational material is approved for release. | Owner gate resolved. |
| B-08 | The technical record for `7acd4c4` was completed and accepted. | The documentation-only commit carrying this record must receive exact post-commit tests, scans, build, wheel, pack, and PGM-boundary verification. Record its SHA/results externally without modifying it. | Pending exact verification of the record-carrying commit. |

## Capability-Specific Blocks And Validation Gaps

These items do not require fabricated replacements. They must remain disabled or
be described accurately unless their stated resolution is completed.

| ID | Capability/status | Required treatment for `0.1.0` | Resolution for later enablement |
| --- | --- | --- | --- |
| C-01 | ChromaDB support is blocked. An audit of `chromadb 1.5.9` found critical `PYSEC-2026-311` / `CVE-2026-45829`, with no fixed version reported on 2026-07-13. | Keep `chromadb` out of every install extra and default path. Retain the adapter only as disabled first-party source, with the limitation documented. | Require a fixed release, fresh vulnerability/license audits, adapter tests, threat-model review, and human security approval. |
| C-02 | EAS, its engineering packs, and MCM have not been independently professionally validated across their possible engineering uses. | Present outputs only as decision support requiring licensed engineering judgment, code/compliance review, safety analysis, and human approval. Do not claim production or regulatory validation. | Independent domain review, test-case traceability, boundary/units review, and documented validation appropriate to each supported discipline. |
| C-03 | SIS candidates have not been independently established as novel, patentable, feasible, safe, or experimentally valid. | Describe outputs as hypotheses/candidates requiring prior-art, patent, safety, feasibility, and experimental review. | External technical and legal validation for the particular claim; no general validation may be inferred. |
| C-04 | Optional live OpenAI, Anthropic, Google, Ollama, ElevenLabs, browser microphone, camera, and cross-browser flows are operator/environment dependent and have not been certified by the deterministic mock suite. | Keep them opt-in, fail closed when unconfigured, disclose data-transfer boundaries, and report unexecuted live tests as gaps. No cloud test may incur charges by default. | Run approved opt-in integration and browser tests using non-production accounts/data; record versions, costs, scopes, privacy review, and exact results. |

## Preserved Release Conditions

- Removing a secret in a later commit does not erase earlier public history.
- A passing automated secret scan does not replace lifecycle analysis,
  revocation where applicable, or manual privacy review.
- A package's open-source label or permissive metadata does not replace review of
  its controlling license and notices.
- Deterministic execution does not prove that an engineering model, constraint,
  pack, or result is correct for a real use.
- A mock-provider pass demonstrates pipeline behavior, not model quality.
- Documenting a limitation does not authorize distribution of material whose
  ownership, privacy, or license status is unresolved.

## Remaining Pre-Push Sequence

1. Create the single documentation-only approval commit without amending the
   verified release-candidate commit.
2. From that exact new commit, rerun evidence, non-network tests, secret/history
   scans, dependency audit, lint, format, security, build, wheel inspection,
   engineering-pack verification, and the public/private PGM boundary check.
3. Record the exact commit, tree, parent, artifact hashes, and verification
   results externally.
4. Obtain a separate explicit authorization before configuring a remote,
   pushing, changing visibility, tagging, or publishing.
5. After a human-controlled push, verify the public repository and CI before a
   later `v0.1.0` tag or release.

Until the exact record-carrying commit passes step 2 and receives separate
remote/push authorization, the branch remains local/private.
