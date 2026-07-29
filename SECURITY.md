<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Security Policy

## Supported Versions

The canonical source repository is public. Until `v0.1.0` is formally tagged
and released, the current `main` release candidate receives security fixes.
After that release, the latest `0.1.x` patch release is expected to receive
security fixes; older snapshots and private forks are not guaranteed support.
This table must be updated when a later series is supported.

| Version | Supported |
| --- | --- |
| Public `main` / `0.1.0` release candidate | Yes |
| Latest tagged `0.1.x` | Yes, after formal release |
| Older / unreleased snapshots | No guarantee |

## Private Reporting

Do not open a public issue for a suspected vulnerability, exposed credential, private data, or exploit.

Preferred channel: use GitHub's **Report a vulnerability** action on the
repository's Security page. Private Vulnerability Reporting was verified
enabled on July 29, 2026.

As a monitored private fallback, email
[security@syntheticoslabs.com](mailto:security@syntheticoslabs.com). This
tested, monitored private reporting address was approved by the release owner
on July 28, 2026.

Include the affected version/commit, component, prerequisites, impact, minimal reproduction, and suggested mitigation. Remove credentials and personal/private data; if a secret is essential to demonstrate impact, first ask how to transfer it securely.

## Response

Maintainers will attempt to acknowledge and triage reports, coordinate a fix, and credit reporters who request credit and acted in good faith. The project does not promise a response or remediation SLA. Do not publish details before maintainers have had a reasonable opportunity to investigate and protect users.

## Scope Priorities

High-priority examples include:

- authentication, session, CSRF, route-authorization, or SSE ownership bypass;
- account-email/user-context confusion across authenticated sessions or requests;
- emergency or urgency claims bypassing authorization or consequential-tool controls;
- credential or private-data exposure;
- cross-session memory, transcript, job, or artifact access;
- arbitrary code execution through MCM, SAL, providers, uploads, or tools;
- unintended microphone/camera activation or sensory retention;
- SSRF or unapproved data transfer through model endpoints;
- dependency or build compromise affecting distributed artifacts.

Model hallucination, prompt quality, unsupported engineering conclusions, and generated-concept novelty are usually product/research limitations rather than software vulnerabilities unless they cross a stated security boundary.

## Current Private Identity-Context Limitation

The private host may supply the account email associated with its authenticated
session to PGM as contextual identity metadata. Carter does not independently
verify real-world identity, and the value must not be treated as authentication
or authorization. Session binding and account-context isolation require further
hardening and dedicated testing before multi-user or network deployment.

Account context should be minimized before provider transfer and redacted from
logs, reports, memory, job metadata, and provider errors. This limitation
concerns the private operational source; the public `0.1.0` research/reference
runtime does not implement that account-context path. See
[docs/PGM.md](docs/PGM.md) and [PRIVACY.md](PRIVACY.md).

The current private PGM includes model-facing emergency-claim and tool-action
guidance. It does not verify emergency statements or deterministically
authorize tools. Consequential actions remain subject to applicable host
authorization, validation, allowlisting, and audit controls.

## Operator Responsibilities

Keep secrets outside source control, run the current patched version, bind local development to loopback, disable debug, use TLS and secure cookies for network access, restrict provider scopes/egress, keep persistence and sensory retention off unless reviewed, and follow [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).

This policy is not a guarantee that the software is free of vulnerabilities.
