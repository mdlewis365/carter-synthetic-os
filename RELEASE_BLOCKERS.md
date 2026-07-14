<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Release Blockers

Release: `0.1.0` (Initial Public Research Release)

Status date: 2026-07-13

**Publication status: blocked pending human review.** No GitHub push, visibility
change, tag, or public release may occur until every publication gate below is
resolved and the confirmations in `PUBLIC_PUSH_CHECKLIST.md` are recorded.

This document distinguishes publication gates from optional capabilities that
are deliberately disabled or have not received external validation. It does not
claim legal, security, scientific, or professional-engineering approval.

## Must Resolve Before Public Push

| ID | Open blocker | Required resolution | Publication effect |
| --- | --- | --- | --- |
| B-01 | First-party authorship, copyright ownership, and AGPL relicensing have not received final human signoff across migrated implementation, snippets, documentation, templates, browser code, and tests. | Owner/counsel reviews the final tree and migration provenance, resolves any joint or employer authorship question, and records authority to distribute every first-party file under `AGPL-3.0-only`. | Blocks all public distribution. |
| B-02 | Patent and invention-disclosure review is incomplete for Carter, SOS, EAS, SIS, CSC, MCM, SAL, engineering packs, and migrated research material. | Owner/counsel identifies patent-sensitive disclosures, confirms publication timing, and approves the final public scope. | Blocks all public distribution. |
| B-03 | Engineering-pack provenance and standards-derived-content review is incomplete. A technical classification as first-party is not legal proof of ownership or redistribution rights. | Review every included pack for author, source, quotation, table, formula, standard, and third-party attribution; remove or rewrite anything not cleared. | Blocks publication of the packs and therefore the current release tree. |
| B-04 | Third-party and transitive license review remains a human legal task. Package metadata and the point-in-time tooling report are not a compatibility opinion. | Review the final resolved dependency inventory, full license texts, notices, optional SDK distribution model, and built wheel; preserve all required notices. | Blocks final release approval. |
| B-05 | Private screenshots found during source/documentation audit contained authentication-like query or token material. Exclusion prevents new-copy exposure but does not establish revocation or erase older repository history. | Confirm every affected credential/token is revoked or expired; scan all branches, tags, releases, issues, and history of the older documentation repositories and any prior publication locations; rotate when status is uncertain. Record no secret values in the resolution. | Blocks making the new repository public. |
| B-06 | `SECURITY.md` intentionally contains an unapproved private-contact placeholder. | Enable and verify GitHub Private Vulnerability Reporting for the canonical repository, or replace the placeholder with an approved private security-reporting contact. Test the selected path before publication. | Blocks making the repository public. |
| B-07 | Final privacy and exclusion review is incomplete. Automated scans cannot prove that memories, conversations, identities, recordings, job payloads, provider identifiers, or operational data are absent. | Human reviewers inspect the final diff, all commits, generated evidence, packaged artifacts, and exclusion report; rerun secret/privacy scans immediately before the first push. | Blocks all public distribution. |
| B-08 | Final release evidence is point-in-time and can be invalidated by later edits. | From the exact proposed public commit, reproduce evidence, run the full non-network suite, run lint/format/security/build checks, inspect the wheel, record exact results, and approve any failures or skips without concealment. | Blocks the first push/tag until complete. |

## Capability-Specific Blocks And Validation Gaps

These items do not require fabricated replacements. They must remain disabled or
be described accurately unless their stated resolution is completed.

| ID | Capability/status | Required treatment for `0.1.0` | Resolution for later enablement |
| --- | --- | --- | --- |
| C-01 | ChromaDB support is blocked. An audit of `chromadb 1.5.9` found critical `PYSEC-2026-311` / `CVE-2026-45829`, with no fixed version reported on 2026-07-13. | Keep `chromadb` out of every install extra and default path. Retain the adapter only as disabled first-party source, with the limitation documented. | Require a fixed release, fresh vulnerability/license audits, adapter tests, threat-model review, and human security approval. |
| C-02 | EAS, its engineering packs, and MCM have not been independently professionally validated across their possible engineering uses. | Present outputs only as decision support requiring licensed engineering judgment, code/compliance review, safety analysis, and human approval. Do not claim production or regulatory validation. | Independent domain review, test-case traceability, boundary/units review, and documented validation appropriate to each supported discipline. |
| C-03 | SIS candidates have not been independently established as novel, patentable, feasible, safe, or experimentally valid. | Describe outputs as hypotheses/candidates requiring prior-art, patent, safety, feasibility, and experimental review. | External technical and legal validation for the particular claim; no general validation may be inferred. |
| C-04 | Optional live OpenAI, Anthropic, Google, Ollama, ElevenLabs, browser microphone, camera, and cross-browser flows are operator/environment dependent and have not been certified by the deterministic mock suite. | Keep them opt-in, fail closed when unconfigured, disclose data-transfer boundaries, and report unexecuted live tests as gaps. No cloud test may incur charges by default. | Run approved opt-in integration and browser tests using non-production accounts/data; record versions, costs, scopes, privacy review, and exact results. |

## Conditions That Do Not Clear A Blocker

- Removing a secret in a later commit does not make earlier public history safe.
- A passing automated secret scan does not replace credential revocation or
  manual privacy review.
- A package's open-source label or permissive metadata does not replace review of
  its controlling license and notices.
- Deterministic execution does not prove that an engineering model, constraint,
  pack, or result is correct for a real use.
- A mock-provider pass demonstrates pipeline behavior, not model quality.
- Documenting a limitation does not authorize distribution of material whose
  ownership, privacy, or license status is unresolved.

## Required Human Review Order

1. Complete authorship, ownership, patent, engineering-pack, and third-party
   license review; remove any material that is not affirmatively cleared.
2. Confirm token/credential revocation and inspect older public documentation
   repository history and publication surfaces.
3. Complete final privacy, security, exclusions, and source/header review.
4. Approve and verify a private vulnerability-reporting channel.
5. Rebuild from the exact proposed commit; rerun evidence, non-network tests,
   secret scan, dependency audit, lint, format, security, and wheel inspection.
6. Review the complete commit history and final diff, then complete every item in
   `PUBLIC_PUSH_CHECKLIST.md`.
7. Only after those approvals, make the first human-controlled push and visibility
   decision. Create the `0.1.0` tag and release only after the public repository is
   independently verified.

Until that sequence is complete, the branch must remain local/private and no
remote release operation is authorized.
