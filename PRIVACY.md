<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Privacy

Carter Synthetic OS is self-hosted research software. The repository itself adds no analytics, advertising trackers, or developer-operated telemetry service. An operator's deployment and selected providers determine the actual data processing.

## Default Data Posture

- Mock mode is local and uses deterministic synthetic fixtures.
- CRM and sensory state are session-scoped and ephemeral.
- Durable memory and sensory retention are disabled by default.
- Raw request/response, audio, transcript, image, and private memory logging is disabled by default.
- Microphone and camera require explicit user action and visible active state.
- Camera support in `0.1.0` is a browser-local preview only.
- No private database, conversation, memory, OpRep, recording, voice asset, or user account ships with the repository.

Ephemeral processing is not a guarantee of cryptographic erasure. Process memory, operating-system swap, crash capture, proxy logs, backups, and provider systems may create additional copies depending on deployment.

## Provider Transfers

Selecting Ollama sends allowed request/transcript context to the configured Ollama endpoint. The safe default is loopback. Selecting OpenAI, Anthropic, or Google sends request data and allowed context to that provider. Selecting Google for CSC transcription sends captured audio. Selecting ElevenLabs sends response text and provider authentication data for TTS.

Those providers control their own retention, model-improvement, abuse-monitoring, residency, subprocessors, billing, and deletion practices under the operator's account and agreement. The project does not select a cloud provider automatically or silently fall back to one.

## Memory And Persistence

The public in-memory stores contain no seeded personal records. CRM, in-memory AMS, sensory state, and job results expire after at most 3600 seconds of session inactivity by default and are also removable through the clear-session route. Browser-close cleanup is best effort; idle expiry is the server-side backstop. SQLite and Chroma are opt-in. Before enabling a durable store, the operator must define lawful purpose, data minimization, access controls, retention period, deletion and export procedures, backup behavior, incident response, and applicable notices/consent.

Retrieved content remains untrusted and can expose sensitive material to a selected provider when included in context. Do not ingest data without authority. Do not use real personal or confidential data in examples or standard tests.

## Sensory Data

Users must deliberately start microphone or camera access and must be able to stop it immediately. Wake-name detection is not consent or authentication. Recording laws and consent requirements vary by location and context; operators and users are responsible for compliance and notice to everyone captured.

Raw audio, TTS audio, and camera frames are not durably retained by the application. Transcript buffers remain only in bounded process memory until explicit clearing, idle expiry, or process exit. Public release `0.1.0` rejects `CARTER_ENABLE_SENSORY_RETENTION=true`; adding durable sensory retention requires a separate implementation and privacy review.

## User Requests

For an operator-run deployment, privacy access, correction, export, and deletion requests must go to that operator. Synthetic OS Labs cannot access or delete data held solely by an independent self-hosted deployment or its providers.

Before the canonical repository is public, an approved project privacy contact is still pending:

**[APPROVED PRIVACY CONTACT TO BE ADDED BEFORE PUBLICATION]**

Do not include personal data in public repository issues.

## Limits

This document describes repository defaults, not a universal privacy policy or compliance certification. Operators must adapt notice and controls to their jurisdiction, data, users, providers, and deployment. See [docs/DATA_FLOW.md](docs/DATA_FLOW.md) and [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).
