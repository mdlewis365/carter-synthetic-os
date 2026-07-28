<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Research Status

Version `0.1.0`, **Initial Public Research Release**, makes implementation available for inspection, testing, and extension. Public availability is not scientific validation or production qualification.

## Status Vocabulary

- **Implemented:** first-party code is present in this repository.
- **Tested:** repository tests exercise a declared behavior; exact results belong in `PUBLIC_RELEASE_REPORT.md`.
- **Experimentally validated:** evaluated against a documented experimental protocol and evidence.
- **Production validated:** operated under documented real-world acceptance criteria and monitoring.
- **Requires independent review:** the repository cannot establish fitness or correctness for a consequential use.

## Component Status

| Component | Implemented | Repository-tested | Experimental / production claim |
| --- | --- | --- | --- |
| Carter request orchestration and streaming host | Yes | Bounded tests planned/provided | No production-validation claim. |
| SOS normalization, context, routing, and governance | Yes | Bounded deterministic tests | No general semantic-correctness claim. |
| CRM and in-memory AMS | Yes | Interface/session behavior | No durable multi-tenant validation. |
| DIM | Bounded new public interface | Contract behavior | No migrated private or production claim. |
| SAL | Bounded new public interface | Normalization behavior | Not a semantic-truth engine. |
| SQLite memory | Optional adapter | Deterministic adapter tests | No production data-service claim. |
| Chroma memory | Disabled adapter boundary | Lazy/disabled behavior only | Dependency blocked by `CVE-2026-45829`; no runtime availability claim. |
| Mock provider | Yes | Deterministic fixture behavior | Not an LM or quality benchmark. |
| Ollama/cloud providers | Optional | Failure/mocked boundary tests by default | Real-service behavior is operator-dependent. |
| MCM | Yes | Supported deterministic calculations | No blanket formula/model suitability claim. |
| EAS | Yes | Workflow/schema/governance behavior | Requires licensed professional review. |
| SIS | Yes | Workflow/schema/evaluator behavior | Candidates require technical, patent, safety, and experimental review. |
| CSC audio/transcript boundaries | Yes | Synthetic/session tests | No medical, surveillance, or safety validation. |
| CSC camera | Local preview boundary only | Browser boundary as available | No server-side interpretation claim. |

## Current Private Snapshot

The private source was reconciled at commit `df0230b` on 2026-07-27.

| Area | Code-backed behavior | Conceptual, pending, or limited behavior |
| --- | --- | --- |
| PGM | AMS/RAG retrieval and assembly of CRM, request, time, configured Carter name, host-provided account context, and prompt policy. Current prompt policy includes revised Prime Directives and emergency-claim/tool-action guidance. | Named model-facing governance responsibilities influence probabilistic generation and are distinct from deterministic Python enforcement. Emergency assertions remain unverified, and consequential actions still require host authorization and controls. |
| SOSP | No reference remains in tracked private files at commit `df0230b`; it was removed from PGM. | Historical references belong only in explicitly dated history. |
| User context | The private host may pass the account email associated with its authenticated session to PGM as contextual identity metadata. | It is not independent identity or authority; session binding and account-context isolation require hardening and testing. |
| Private CSC | Explicit hearing, Gemini transcription, basic priority metadata, session transcript buffer, manual local Ollama interpretation, and configurable TTS. | Interpretation is not automatically submitted to Carter or PGM; AAM priority triage, SAL semantic adjudication, candidate queueing, automatic response/TTS integration, and camera handling remain planned. |

See [PGM.md](PGM.md) for the evidence boundary. These entries describe the
private implementation and do not change the public component-status table.

## Evidence Interpretation

The checked-in evidence case proves that the included code can execute one synthetic deterministic workflow and generate the recorded artifacts and hashes under the reported environment. It does not prove performance on private data, general model intelligence, engineering fitness, invention novelty, or production security.

No benchmark, uptime, cost, latency, accuracy, safety, or deployment claim should be added without a reproducible method, raw results that can legally be published, and clear limitations.

## Review Expectations

Research users should record software/model versions, configuration, prompts or inputs that can lawfully be retained, deterministic artifacts, uncertainties, failed runs, and human-review decisions. Consequential conclusions require independent domain methods and should not rely on generated narrative alone.
