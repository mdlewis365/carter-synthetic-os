<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Data Flow

This document describes the public `0.1.0` paths. The repository contains no production memories, conversations, provider credentials, recordings, camera images, vector databases, SQLite databases, logs, or OpRep transcripts.

## Carter Request

1. The browser submits a request under a Flask session.
2. The application validates request size, content type, CSRF/session state, and workflow fields.
3. Carter creates a normalized request with opaque identifiers and a content hash.
4. SOS assembles bounded session context and explicit temporal/context anchors.
5. The selected provider receives the prompt and allowed context.
6. Governance classifies the candidate and permits, limits, or blocks the response.
7. Server-Sent Events expose status/final events only to the owning session.
8. The event recorder stores redacted metadata and hashes, not prompt/response text.

With a cloud provider, step 5 crosses the local trust boundary. With Ollama on loopback, it crosses into the operator's local Ollama process. With mock mode, it remains in process.

## Specialized Workflows

EAS can pass a model-produced structured plan into schema validation and then the supported subset into MCM. Deterministic results, EDR, and governance metadata are used to produce the final advisory output. Authorized supporting-file content, if enabled by the host, must be bounded and treated as untrusted.

SIS passes structured scientist input to candidate generation, evaluator interfaces, optional deterministic feasibility checks, and output governance. It includes no patent database lookup or automatic confidential-invention store.

CSC passes browser audio, after explicit activation, to the selected transcription boundary. Transcript text is classified and held in a session buffer. Optional Ollama interpretation receives bounded transcript context. Optional TTS sends response text to the configured provider. The camera boundary is local preview only.

## Data Categories

| Category | Default location | Default retention | Possible external transfer |
| --- | --- | --- | --- |
| Request and response text | Process/session memory | Bounded session with idle expiry | Selected Ollama or cloud model provider. |
| CRM context | Process/session memory | Bounded session with idle expiry | Included as allowed provider context. |
| AMS records | Empty/in-memory adapter | None across restart | Only if operator enables persistence and provider context use. |
| Event/OpRep metadata | Process or generated evidence files | Metadata only | None by core behavior. |
| EAS/SIS payloads | Process/session memory | Job TTL, at most 15 minutes by default | Selected model provider. |
| Microphone audio | Browser/process memory | No retention | Selected cloud transcription provider. |
| Transcript | Session buffer | No durable retention | Selected interpretation/model provider. |
| Camera frames | Browser local preview | No retention | No server transfer in `0.1.0`. |
| TTS text/audio | Process/browser memory | No retention | Text to selected TTS provider. |
| Credentials | Operator environment | Operator-controlled | Sent only as provider authentication. |

## Persistence

`CARTER_ENABLE_MEMORY=false` and `CARTER_ENABLE_SENSORY_RETENTION=false` are the safe defaults. Release `0.1.0` rejects attempts to set sensory retention true. SQLite is a separate opt-in memory store; enabling it changes the privacy and security posture and requires operator-defined retention, access, backup, deletion, and incident-response procedures. Chroma adapter source is present, but no dependency is declared while `CVE-2026-45829` remains unresolved for the current package line.

No raw-content logging should be inferred from an event ID or artifact hash. Evidence artifacts use synthetic input and explicitly generated outputs.

## Browser And Session Boundary

Session cookies must be protected by suitable secure, HTTP-only, and same-site settings for the deployment. Credentials do not belong in query strings or browser persistent storage. A job identifier is not authorization; every result and SSE request must also match the owning session.

## Deletion And Shutdown

Ephemeral in-process data is removed when its session is reset, the application discards it, or the process terminates. This is not a cryptographic erasure guarantee. When an operator enables a durable adapter or a cloud provider, deletion must also cover databases, vector indexes, backups, provider systems, and derived artifacts.
