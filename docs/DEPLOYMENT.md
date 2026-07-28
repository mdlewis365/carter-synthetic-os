<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Deployment

Carter Synthetic OS `0.1.0` is an initial public research release for Python 3.11 or newer. The included server is suitable for local evaluation and controlled development. It is not presented as a production-hardened, multi-tenant service.

## Safe Local Defaults

The example configuration binds to loopback and disables debug, persistence, and sensory retention:

```dotenv
CARTER_HOST=127.0.0.1
CARTER_PORT=5000
CARTER_DEBUG=false
CARTER_PROVIDER=mock
CARTER_ENABLE_MEMORY=false
CARTER_ENABLE_SENSORY_RETENTION=false
CARTER_SESSION_IDLE_TTL_SECONDS=3600
CARTER_SESSION_COOKIE_SECURE=false
```

`CARTER_ENABLE_SENSORY_RETENTION=true` is rejected in this release. The idle
TTL applies to process-local CRM, AMS, CSC state, and associated session data;
it is not a substitute for an operator retention policy when durable adapters
are enabled.

Use `.env.example` as a placeholder reference and export configuration through the process environment. The application does not require or automatically load a dotenv file. If local tooling creates one, replace `FLASK_SECRET_KEY` with a long random value and keep the file untracked. After setup, start the mock demonstration with `./scripts/run_demo.sh` on POSIX or `.\scripts\run_demo.ps1` on PowerShell. The root README records the full quick start.

Do not bind to a non-loopback address simply to work around browser or proxy configuration. A reachable deployment needs a documented authentication design, TLS, reverse-proxy limits, security headers, CSRF protection, secure cookie settings, monitoring, patching, and incident response.

`CARTER_SESSION_COOKIE_SECURE` defaults to `false` for the loopback HTTP
demonstration. Set it to `true` whenever the browser uses HTTPS. This switch
only marks the cookie `Secure`; it does not configure TLS, authenticate users,
validate proxy headers, or supply the other missing deployment controls.

The configuration rejects non-loopback `CARTER_HOST` values unless an operator explicitly sets `CARTER_ALLOW_PUBLIC_BIND=true`. That opt-in only acknowledges the changed boundary; it does not add the missing production controls.

## Local Model

Ollama is separately installed and operated. Keep `OLLAMA_BASE_URL` on `http://127.0.0.1:11434` unless a reviewed deployment explicitly permits a remote endpoint. Pull model weights separately and review the model's license. The application reports an unavailable provider when the service or configured model cannot be reached.

## Cloud Providers

Install only the required optional extra and set credentials in the process environment or a proper secret manager. Do not bake keys into images, source, `.env.example`, service definitions, or frontend configuration. Establish provider data-processing, retention, residency, access, and billing controls before sending real data.

## Persistence

The default in-memory implementation is appropriate for the synthetic demonstration. If SQLite is enabled:

- place data outside the source tree;
- restrict filesystem permissions;
- define retention and deletion;
- encrypt host storage and backups where required;
- separate tenants and environments;
- never reuse the excluded private stores;
- test recovery and deletion procedures.

SQLite is not configured as a production high-availability service by this repository. ChromaDB must not be enabled from the affected 1.x dependency line; see `RELEASE_BLOCKERS.md`.

## CSC

Microphone and camera APIs generally require a secure browser context outside loopback. Preserve explicit activation and visible active-state controls. Do not enable sensory retention by default. Cloud transcription and TTS require an affirmative disclosure because audio or text leaves the local process.

## Production Hardening Gap

A public network deployment requires work beyond this release, including an approved identity provider, authorization model, rate limiting, request quotas, process isolation for tools, malware/content controls for uploads, outbound network policy, centralized secret management, encrypted storage, audit-retention rules, observability, backups, and a tested vulnerability/incident process.

No Cloudflare tunnel configuration, production domain, production account, or deployment token is included. Docker support is omitted rather than implying a maintained production image.

## Current Private Host Difference

The safe-default and optional-provider statements above apply to the public
`0.1.0` research/reference implementation, not the full private host. The
private host has different startup, provider, persistence, identity, and
deployment assumptions and requires a separate security and configuration
review before network or multi-user use. The maintained Carter deployment is
authentication-protected, and guided or demonstration access may be available
upon request. That fact does not transfer the private authentication
implementation or its assurances to this public reference runtime. See
[PGM.md](PGM.md) and [Threat Model](THREAT_MODEL.md).

## AGPL Network Use

The software is licensed under `AGPL-3.0-only`. Operators who modify and run it for users over a network should review the license's corresponding-source requirements. The interactive interfaces expose a license view and canonical source link; deployments must preserve applicable notices. This statement is informational, not legal advice.
