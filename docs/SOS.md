<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Synthetic Operating System

Synthetic Operating System (SOS) is the coordination layer beneath Carter and the specialized EAS, SIS, and CSC workflows. It provides bounded contracts for normalization, context assembly, memory, provider routing, governance, semantic adjudication, tool invocation, and operational metadata.

## Public Modules

| Module | Public responsibility |
| --- | --- |
| `sos.orchestration` | `NormalizedRequest`, request normalization, temporal/context anchors, `ContextAssembly`, and pipeline execution. |
| `sos.memory` | `RollingContextMemory`, `InMemoryAMS`, `DIMIngestor`, optional SQLite, and a disabled Chroma adapter boundary. |
| `sos.models` | Provider-neutral requests/responses, provider construction, and typed provider failures. |
| `sos.governance` | Risk/status decisions and an allowlisted tool boundary. |
| `sos.sal` | Bounded JSON-object normalization and structural validation; broader semantic adjudication remains architectural intent. |
| `sos.computation` | MCM deterministic calculation, units, constraints, selection, and supported sensitivity behavior. |
| `sos.logging` | LCM redacted bounded metadata events and metadata-only OpRep records. |
| `sos.registry` | Explicit subsystem/provider registration. |

These modules are application components, not an operating-system kernel and not a security boundary equivalent to an OS process sandbox.

## Orchestration

For a normal Carter request, SOS:

1. validates and normalizes user input without changing its substantive intent;
2. creates explicit time, session, and request anchors;
3. obtains only the session context allowed for the workflow;
4. assembles a structured provider request;
5. invokes the configured provider through a provider-neutral boundary;
6. normalizes the returned candidate where a structured response is required;
7. applies deterministic governance rules;
8. returns the response and redacted execution metadata.

EAS and SIS add their own workflow-specific stages. CSC places transcription and interpretation behind separate sensory boundaries.

## Deterministic And Probabilistic Behavior

| Operation | Classification |
| --- | --- |
| Request field validation and normalization | Deterministic for a given input and version. |
| Session context limits and deduplication rules | Deterministic. |
| Schema validation and JSON normalization | Deterministic. |
| MCM arithmetic, unit checks, constraints, and supported sensitivity calculations | Deterministic for a validated plan and runtime version. |
| Governance status classification | Deterministic rule evaluation. |
| Mock provider fixtures | Deterministic demonstration behavior; not a language model. |
| Ollama and cloud model generation | Probabilistic, subject to provider and model behavior. |
| Model-produced plan, interpretation, report prose, or invention candidate | Probabilistic until and unless a specific field is deterministically validated. |

Deterministic validation does not make an upstream model statement true. It establishes only the condition named by the validator, such as schema conformance, a repeatable calculation, or a policy classification.

## Memory And Context

CRM is the bounded rolling context for the active session. AMS is a long-term-memory interface with safe in-memory and opt-in storage implementations. DIM is an ingestion/deduplication contract introduced for this public release. No active private DIM module was found, and the release does not present DIM as a migrated production subsystem. See [MEMORY.md](MEMORY.md).

Context assembly gives the current request priority over recalled content. Memory and retrieval output are annotated context, not authoritative instructions. The public repository includes no production conversation database, vector index, seeded personal memory, or private OpRep.

The privacy-sensitive private PGM prompt/identity assembly is not copied. Its public architectural role is represented by generic normalization, explicit anchors, structured context assembly, and governance. There is no separate full RAG subsystem in `0.1.0`; Chroma adapter source is included without a declared dependency, corpus, or embedding model because the current dependency line is blocked by `CVE-2026-45829`.

In the current private implementation, PGM means **Prompt Governance Module**.
It performs AMS/RAG retrieval and assembles those sources with CRM conversation,
the request, timestamp, configured Carter name, account context, and prompt-level
policy. Its named modules express model-facing governance responsibilities
through prompt construction and are distinct from deterministic Python
enforcement. Authentication and authorization remain host controls. See
[PGM.md](PGM.md).

## Governance, SAL, And Tools

Governance returns a bounded status and review requirement based on structured
signals. In the packaged non-mock EAS/SIS provider adapter, SAL normalizes one
structured model object and returns a controlled result. Carter chat, CSC,
memory, MCM, and generic orchestration do not call it. `sos.sal` does not log or
persist adjudication outcomes and does not prove semantic truth. Tool execution
is deny-by-default and limited to registered callables and validated arguments.
The public tool boundary does not create arbitrary shell or unrestricted
network access.

## Model Routing

`create_provider` selects and configures an implementation without contacting the service:

- `mock` is the default, requires no credentials, and returns clearly labeled synthetic fixtures;
- `ollama` communicates with an operator-run local service on loopback by default;
- `openai`, `anthropic`, and `google` require optional packages and operator-supplied credentials.

Optional integrations fail with a controlled provider error when dependencies, configuration, or services are unavailable. Public error codes include `missing_api_key`, `model_not_configured`, `missing_dependency`, `generation_failed`, and Ollama `unavailable`; provider exception details are not exposed as successful output. The core installation and standard tests require no network and incur no API charges.

## Logging And Operational Reports

The logging boundary records execution metadata such as subsystem, status, timing, backend label, and artifact hashes. Raw prompts, model responses, transcripts, audio, images, credentials, and session cookies are not normal log fields. Raw-content retention is disabled by default.

LCM and OpRep in this release refer to bounded event/report generation, not a migrated private raw conversation store. Operators adding a persistence backend are responsible for access control, retention, deletion, and disclosure policy.

## Failure Behavior

Validation failures, unavailable providers, unsupported deterministic plans, and governance review requirements remain explicit. The pipeline must not replace them with a successful-looking fabricated result. A caller receives a typed or structured failure suitable for the web layer to present without exposing credentials, stack traces, or private request content.

## Current Limits

- The public DIM and SAL implementations are bounded `0.1.0` interfaces.
- SQLite persistence is opt-in and is not a production data service. ChromaDB is unavailable pending an audited upstream fix.
- Local and cloud model quality depends on separately obtained models and services.
- Governance is a software control, not certification, legal review, or professional approval.
- The public release contains no unrestricted autonomous execution loop.
