<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Migration From Documentation-Only Repositories

The canonical project is intended to move from three documentation-only repositories to `mdlewis365/carter-synthetic-os` after this monorepository is public and verified:

- `synthetic_operating_system`
- `engineering-assistance-system`
- `synthetic-ideation-system`

## What Changes

The monorepository contains runnable first-party implementation, tests, examples, packaging, web interfaces, and unified architecture/legal documentation for Carter, SOS, EAS, SIS, and CSC. Older documentation described private behavior at a public-safe conceptual level; those repositories are not package dependencies and their private-implementation notices do not describe this release.

Terminology and claims are tightened:

- Carter is described as a governed compound AI expert system and research platform.
- Deterministic and probabilistic boundaries are explicit.
- DIM and SAL are labeled as new bounded `0.1.0` public interfaces.
- Public SIS evaluator/MCM coordination is labeled as new, not as a previously active private route.
- CSC camera capability is limited to explicit local preview.
- EAS and SIS carry mandatory professional/independent review warnings.

## Licensing

Historical versions of the documentation-only repositories remain available under the BSD-3-Clause licenses that accompanied them. Those grants are not revoked. The new monorepository is licensed under `AGPL-3.0-only`; do not copy text/code between versions without preserving and reconciling applicable notices.

## Links And References

After the new repository is public, tested from a fresh clone, and source/legal links are verified:

1. Update old repository READMEs to identify the new canonical repository.
2. Update external documentation and package links.
3. Preserve historical license and notices in the old repositories.
4. Consider archiving the old repositories only after links and migration guidance are live.

Archival/redirection is a later human action. This local release-preparation work does not modify, archive, or push any older repository.

## No Data Migration

Do not migrate production memories, CRM data, Chroma/SQLite/PostgreSQL stores, OpReps, jobs, logs, credentials, recordings, screenshots, or user accounts. Public demonstrations begin with empty/synthetic state.

