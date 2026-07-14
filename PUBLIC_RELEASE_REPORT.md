<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Public Release Report

Release: `0.1.0` - Initial Public Research Release

Preparation date: 2026-07-13

Branch: `release/carter-agpl-public`

Publication status: **local preparation complete; public push blocked pending
the human gates in `RELEASE_BLOCKERS.md` and `PUBLIC_PUSH_CHECKLIST.md`.**

## Systems Released

- **Carter:** governed conversational runtime, provider selection, structured
  context, bounded session continuity, synchronous and SSE response paths,
  subsystem routing, and a runnable Flask interface.
- **Synthetic Operating System:** orchestration contracts, temporal/context
  anchors, CRM, AMS-compatible interfaces, DIM ingestion/deduplication, LCM
  metadata events, operational reports, SAL adjudication, tool boundaries,
  registry, deterministic governance, provider adapters, SQLite, and a
  source-visible but dependency-blocked Chroma boundary.
- **Engineering Assistance System:** five modes, deterministic and
  provider-planned stage-one schemas, pack selection, full MCM request and
  computation path, units, constraints, sensitivity interfaces, Engineering
  Decision Records, governance classification, advisory generation, and
  mandatory professional-review gating.
- **Synthetic Ideation System:** scientist-input normalization, mechanism,
  hybrid, architecture, process, algorithmic, and constraint-inversion modes,
  candidate schemas, invariant/rejection/novelty evaluators, optional MCM
  feasibility, aggregate governance, and hypothesis-only outputs.
- **Carter Sensory Console:** session-isolated hearing/camera/playback state,
  browser WAV capture, wake-name attention classification, bounded transcript
  buffer, strict interpretation/transcription normalization, optional local
  Ollama interpretation, configurable ElevenLabs HTTPS TTS, and explicit
  privacy indicators. Camera processing is local preview only.

The release describes Carter as a governed compound AI expert system and
research platform. It makes no consciousness, sentience, AGI, unrestricted
autonomy, professional approval, scientific validation, or production-readiness
claim.

## Migration And File Scope

The final release tree contains 190 tracked files after this report is added.
It includes 93 files under `src`, 16 public test modules, 23 example/evidence
files, 15 subsystem/operations documents, six setup/run/test scripts, and eight
GitHub community/automation files.

Cleared first-party implementation migrated or adapted into the monorepository
includes the complete deterministic MCM, Engineering Decision Record helpers,
EAS governance gate, 18 reviewed engineering-pack Markdown files (including
their pack README), cleared SIS schema/evaluator modules, and public SOS
contracts. Security- or privacy-sensitive monolithic Carter, SOS memory,
provider, UI, and CSC behavior was reimplemented as modular public code rather
than copied byte for byte.

Every excluded source/data/asset class, replacement decision, and runtime
effect is recorded in `EXCLUSIONS.md`. Private Git history was not copied.

## Architecture Changes

- Split the production-style Flask monolith into importable `carter`, `sos`,
  `eas`, `sis`, `csc`, and `shared` packages without changing the essential
  five-system boundaries.
- Replaced global/private state with opaque session ownership, bounded
  in-memory jobs, idle expiry, explicit clear operations, CSRF checks, and
  owner-checked job/SSE access.
- Added a deterministic, clearly labeled mock provider and synthetic fixtures
  as the default operating mode; no language model is implied or invoked.
- Made OpenAI, Anthropic, Google, Ollama, transcription, and TTS boundaries
  lazy, optional, and controlled by environment configuration.
- Separated probabilistic planning from schema validation, deterministic MCM
  computation, run-health evaluation, governance, and human approval.
- Added public DIM and SAL boundaries and a local camera-preview boundary;
  these are explicitly labeled as new 0.1.0 implementations rather than
  migrated production components.
- Replaced raw/private logs and operational reports with redacted metadata and
  artifact hashes.

## Configuration And Security Changes

- Added a placeholder-only `.env.example`; no dotenv file is loaded
  automatically and placeholder signing secrets are replaced by ephemeral
  process secrets.
- Defaults are mock provider, `127.0.0.1` bind, Flask debug off, remote Ollama
  rejected, durable memory off, sensory retention rejected, microphone/camera
  off, and a 3600-second in-process idle TTL.
- No production domain, tunnel, user account, database, voice ID, memory,
  recording, report, log, absolute local path, or operational credential was
  included.
- Raw audio uses a bounded `audio/wav` request body so multipart upload spooling
  is not part of the public sensory path.
- Non-finite MCM and sensory values, oversized/deep expressions, sequence
  arithmetic, unsafe exponents, failed constraints, and unhealthy computation
  states are rejected or routed to human review.
- ChromaDB was removed from every package extra after `chromadb 1.5.9` triggered
  critical `PYSEC-2026-311` / `CVE-2026-45829` with no fixed release reported.

See `SECURITY_RELEASE_AUDIT.md`, `PRIVACY.md`, and
`docs/THREAT_MODEL.md` for the complete boundary and remaining-risk record.

## Tests Added And Executed

The public suite covers configuration, secret-free startup, request and schema
normalization, CRM/AMS/DIM/SQLite interfaces, governance, SAL, bounded MCM
computation, units/constraints/run health, EAS pack and EDR workflows, SIS mode
and evaluator behavior, CSC session isolation and non-finite JSON handling,
wake-name classification, provider failures, authorization, SSE, legal/source
notices, and mock end-to-end execution.

Authoritative non-network command:

```console
python -m pytest -m "not local_model and not cloud_provider"
```

Authoritative result on Windows, Python 3.12.4, pytest 8.3.4,
pytest-cov 6.3.0:

| Metric | Result |
| --- | ---: |
| Tests collected | 169 |
| Passed | 169 |
| Failed | 0 |
| Skipped | 0 |
| Source statements | 13,378 |
| Branch-aware coverage | 32% |

The coverage value includes the full migrated 17,000-line MCM module rather
than excluding it to inflate the result. No standard test used the network,
provider credentials, paid APIs, a microphone, camera hardware, or model
weights.

Additional verification completed:

- `ruff check --no-cache .`: passed with Ruff 0.15.21;
- `ruff format --check --no-cache .`: 91 files already formatted;
- main Bandit source scan: passed with Bandit 1.9.4;
- separately bounded MCM Bandit scan: passed with only documented false-positive
  rule classes `B105`, `B112`, and `B608` disabled for that module;
- `python -m examples.evidence.run_case --check`: evidence self-consistent and
  semantically reproducible;
- JavaScript syntax check: passed with `node --check`;
- sdist and wheel: built successfully with build 1.2.1, setuptools 80.9.0,
  and wheel 0.45.1;
- installed-wheel smoke: health, AGPL license, evidence manifest, and 18 pack
  Markdown files available; `License-Expression` is `AGPL-3.0-only`; no
  ChromaDB requirement is declared;
- final safe all-extras environment: 63 third-party distributions, `pip check`
  clean, and pip-audit 2.10.1 reported no known vulnerabilities.

Live cloud, Ollama, ElevenLabs, microphone, camera, and cross-browser tests were
not executed. They remain opt-in validation gaps, not hidden passes.

## Reproducible Evidence

`examples/evidence` performs one continuous deterministic EAS execution from
synthetic input through normalization, structured plan, schema validation,
MCM computation, governance, final advisory, execution metadata, and SHA-256
manifest. Checked-in output is code-generated, not manually presented as
runtime evidence.

Regenerate:

```console
python -m examples.evidence.run_case
```

Verify without replacing the recorded runtime metadata:

```console
python -m examples.evidence.run_case --check
```

## Documentation Created

The root README covers project status, accurate Carter scope, architecture,
all five subsystems, quick start, mock/Ollama/cloud modes, configuration,
testing, privacy, security, deployment, limitations, licensing, contribution,
roadmap, source availability, and attribution. Seven required lifecycle and
boundary diagrams are supplied as Mermaid source across the README and docs.

Subsystem and operational documentation includes architecture, SOS, memory,
governance, SAL, EAS, SIS, CSC, providers, data flow, deployment, threat model,
testing, limitations, and research status. Community, security, privacy,
copyright, trademark, contribution, conduct, release, migration, roadmap,
notices, and issue/PR files are included.

## Licensing

First-party source is marked `SPDX-License-Identifier: AGPL-3.0-only` with the
stated 2023-2026 copyright notice. `LICENSE` contains the official unmodified
GNU Affero General Public License version 3 text, and the installed wheel
includes the license. Interactive routes display copyright, AGPL-only,
no-warranty, license-view, and canonical source-code notices.

Third-party dependencies and services retain their own licenses and terms.
`LICENSE_COMPATIBILITY_REPORT.md` is a technical inventory, not legal advice.

## Known Limitations And Blockers

- Publication remains blocked on human copyright/IP/patent, engineering-pack,
  transitive-license, privacy, final-history, and final-artifact review.
- Tokens visible in excluded legacy screenshots must be revoked or confirmed
  expired, and older public documentation histories must be audited.
- `SECURITY.md` needs an approved private reporting channel before visibility
  changes.
- Chroma-backed persistence is unavailable pending an audited fixed release.
- The mock provider proves pipeline behavior only; it is not a language model
  or quality benchmark.
- EAS/MCM and packs are not professionally, regulatorily, or production
  validated. Every result requires qualified independent review.
- SIS cannot establish novelty, patentability, feasibility, safety, or
  experimental validity.
- CSC camera support is local preview only; durable sensory retention is not
  implemented; optional provider/hardware behavior is not certified.
- The Flask server is a research/development runtime, not a production identity
  or high-availability platform.

The maintained lists are `KNOWN_LIMITATIONS.md`, `docs/LIMITATIONS.md`, and
`RELEASE_BLOCKERS.md`.

## Recommended Human Review Sequence

1. Review authorship, employer/contract rights, patents, all engineering packs,
   prior BSD documentation grants, and third-party licenses/notices.
2. Revoke/confirm excluded screenshot tokens and audit every older public
   documentation branch, tag, release, issue, and commit.
3. Review the complete final tree, exclusions, privacy model, threat model,
   generated evidence, package contents, and all local commits.
4. Approve and test a private vulnerability-reporting channel.
5. From the exact proposed commit, rerun tests, coverage, evidence, Ruff,
   Bandit, detect-secrets, history searches, dependency audit, build, and wheel
   smoke checks on supported Python versions.
6. Complete every confirmation in `PUBLIC_PUSH_CHECKLIST.md` and document any
   accepted residual risk.
7. Only then perform the first human-controlled push and visibility decision.
   Verify public CI before creating the later `v0.1.0` tag or release.

No remote was configured and no remote push, visibility change, tag, or release
was performed during this preparation.
