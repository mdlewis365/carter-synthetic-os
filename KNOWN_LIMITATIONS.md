<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Known Limitations For 0.1.0

- This is an initial public research release, not a production-qualified multi-user service.
- The deterministic mock provider proves pipeline execution only; it is not a language model or benchmark.
- Ollama and cloud models are separately installed/configured and may vary in behavior, resource use, license, availability, and cost.
- DIM and SAL are bounded new public interfaces with limited release history.
- Public SQLite persistence is opt-in and not production validated. Chroma adapter source is present, but its dependency is blocked by `CVE-2026-45829` and is not installed by any release extra.
- Governance validates stated rules/statuses, not the truth of arbitrary model prose.
- EAS results require licensed professional review and do not establish safety, code compliance, or approval.
- SIS outputs require technical validation, prior-art and patent analysis, safety assessment, and experiments.
- SIS contains no patent-search/clearance engine.
- CSC wake-name classification is not identity, consent, or authentication.
- CSC camera support is local browser preview only; no server-side vision interpretation is included.
- Durable memory and sensory retention are off by default; bounded session context remains in process until clear, idle expiry, or process exit.
- The server has not been claimed as independently penetration tested or production hardened.
- The public research/reference runtime is not behaviorally identical to the
  full private host. Current PGM, account-context, and CSC differences are
  maintained in `docs/PGM.md`, `docs/CSC.md`, and `docs/LIMITATIONS.md`.
- Dependency, model, engineering-pack, authorship, IP, and patent reviews retain human blockers before publication.

The maintained detailed discussion is [docs/LIMITATIONS.md](docs/LIMITATIONS.md). Exact test failures, skips, and release blockers belong in the final public release reports and must not be hidden.
