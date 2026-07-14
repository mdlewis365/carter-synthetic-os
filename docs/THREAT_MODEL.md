<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Threat Model

This is a release-oriented threat model for the public `0.1.0` architecture. It is not a penetration-test report or a guarantee of security.

## Protected Assets

- provider credentials and Flask signing secret;
- user requests, session context, memories, transcripts, audio, and camera state;
- EAS/SIS inputs and generated intellectual work;
- authorization state, jobs, SSE results, and generated artifacts;
- host filesystem, network access, tools, and provider billing capacity;
- integrity of deterministic calculations, governance decisions, and evidence hashes.

## Trust Boundaries

The browser/server session, request/parser boundary, model-provider boundary, memory adapters, optional tool boundary, sensory device/provider boundary, and dependency/build pipeline are separate trust boundaries. Model output, retrieved memory, uploaded content, transcripts, and client-supplied identifiers are untrusted.

## Threats And Controls

| Threat | Included control | Remaining risk / operator action |
| --- | --- | --- |
| Credential disclosure | Environment-only configuration, placeholders, redacted events, secret scans, `.gitignore`. | Use a secret manager, rotate keys, inspect logs/history, and limit provider scopes. |
| Cross-session job or transcript access | Session-keyed state and ownership checks on routes/SSE. | Add mature identity/authorization before multi-user deployment and test proxy/cookie settings. |
| CSRF/session theft | Session-bound requests, no query tokens, secure deployment guidance. | Configure HTTPS, secure cookies, origin/CSRF controls, short sessions, and XSS defenses. |
| Prompt injection through input or memory | Structured context roles, precedence rules, schema validation, allowlisted tools. | Models may still follow malicious content; isolate powerful tools and require review. |
| Arbitrary code/expression execution | MCM accepts a bounded expression/operation set; SAL parses data; tool registry is allowlisted. | Audit new operations and run high-authority tools in a separate sandbox. |
| SSRF or data exfiltration through providers | Loopback Ollama default, explicit remote opt-in, provider selection. | Enforce egress allowlists, DNS/IP validation, timeouts, and network isolation. |
| Unbounded input / denial of service | Request and context bounds, bounded buffers, controlled failures. | Add proxy body/time limits, concurrency limits, queues, rate limits, and resource monitoring. |
| Sensitive logging | Metadata/hashes rather than raw content; retention disabled by default. | Inspect framework/proxy/provider logs and crash reporting; hashes may still be correlatable. |
| Media capture without consent | Devices disabled by default, explicit activation, visible state, immediate stop. | Browser compromise or misleading embedding can bypass user expectations; use permissions policy and HTTPS. |
| Cloud privacy/cost exposure | Optional providers, lazy imports, no implicit cloud fallback. | Provider accounts control retention and billing; configure quotas and obtain consent. |
| Malicious or vulnerable dependency | Minimal core, optional extras, pinned/declared metadata, CI audit workflows. | Audits are point-in-time; review advisories, lock deployments, and verify model licenses separately. |
| Calculation/report overclaim | Schema validation, deterministic recomputation, status classification, mandatory warnings. | Incorrect inputs/models can produce plausible errors; professional and experimental review remains mandatory. |

## Abuse Cases

The project should not be deployed as an unrestricted execution agent, covert recording system, identity/authentication system based on wake words, source of professional engineering approval, automated patent-clearance system, or safety/emergency monitor. Controls are designed around bounded research and decision-support workflows.

## Security Assumptions

The host operating system and Python runtime are trusted. An administrator with process or filesystem access can read in-memory data and environment secrets. The application does not protect against a malicious host owner. Browser users are assumed to control their own media consent; a deployment embedding or modifying the UI can violate that assumption.

## Residual Risks

Prompt injection, model hallucination, unsafe provider behavior, dependency compromise, traffic analysis, hash correlation, denial of service, and operator misconfiguration remain possible. The public session mechanism is not a full production identity platform. New DIM, SAL, SQLite, disabled Chroma adapter, and camera-preview boundaries have limited release history. ChromaDB is omitted from dependencies because of `CVE-2026-45829`.

Report suspected vulnerabilities through the private channel described in [SECURITY.md](../SECURITY.md). Do not include secrets or personal data in a public issue.
