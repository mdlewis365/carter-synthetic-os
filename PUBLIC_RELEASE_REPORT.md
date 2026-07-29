<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Public Release Report

Release: `0.1.0` - Initial Public Research Release

Preparation date: 2026-07-28

Reconciliation update date: 2026-07-29

Historical preparation branch: `release/carter-agpl-public`

Public branch: `main`

Pre-reconciliation public baseline, verified 2026-07-29:
`396deb6d5f2b86bde46c6d6ac4e18f448f4ed941`

Publication status: **the canonical source repository is public and
release-owner decisions B-01 through B-07 are resolved or accepted. Version
`0.1.0` had not been tagged or released as of this reconciliation, which
creates or authorizes neither action.**

> **Current-documentation note:** The candidate was prepared on 2026-07-13,
> technically reverified on 2026-07-25, reconciled and retested against the new
> committed private reference on 2026-07-27, and received the recorded
> release-owner decisions on 2026-07-28. This is a report on the public
> candidate, not a current private-source inventory. The bounded comparison uses
> private commit `df0230b`; see `docs/PGM.md` and
> `PROVENANCE_AND_ARCHITECTURE_REVIEW.md` for the implementation findings.
> Dated preparation evidence is retained below. The reconciliation snapshot is
> stated explicitly rather than rewriting that earlier evidence.

## Systems Released

Carter is the flagship implementation of Synthetic OS. EAS and SIS are
functional systems operating within Carter, and CSC is the Carter Sensory
Console.

- **Carter:** governed conversational runtime, provider selection, structured
  context, bounded session continuity, synchronous and SSE response paths,
  subsystem routing, and a runnable Flask interface.
- **Synthetic Operating System:** orchestration contracts, temporal/context
  anchors, CRM, AMS-compatible interfaces, DIM ingestion/deduplication, LCM
  metadata events, operational reports, SAL structural-output normalization,
  tool boundaries,
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

The verified public tree contains 193 tracked files. `docs/PGM.md` is committed
and public, not proposed or untracked. The tree includes 93 files under `src`,
16 public test modules, 23 example/evidence files, 16 subsystem/operations
documents, six setup/run/test scripts, and eight GitHub
community/automation files.

Cleared first-party implementation migrated or adapted into the monorepository
includes the large directly derived or adapted deterministic MCM kernel,
Engineering Decision Record helpers, EAS governance gate, 18 included
engineering-pack Markdown files (including their pack README), cleared SIS
schema/evaluator modules, and public SOS contracts. Release-owner authorship,
ownership, and engineering-pack provenance decisions were recorded on July 28,
2026. This owner disposition is not a legal opinion or independent
professional validation.
Security- or privacy-sensitive monolithic Carter, SOS memory, provider, UI, and
CSC behavior was reimplemented as modular public code rather than copied byte
for byte.

Every excluded source/data/asset class, replacement decision, and runtime
effect is recorded in `EXCLUSIONS.md`. Private Git history was not copied.

## Architecture Changes

- Split the production-style Flask monolith into importable `carter`, `sos`,
  `eas`, `sis`, `csc`, and `shared` packages while preserving the essential
  Carter/Synthetic OS functional boundaries.
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
- Reduced response metadata to configuration-presence booleans instead of
  returning provider model identifiers, and removed the session-derived TTS
  response header.

## Configuration And Security Changes

- Added a placeholder-only `.env.example`; no dotenv file is loaded
  automatically and placeholder signing secrets are replaced by ephemeral
  process secrets.
- Defaults are mock provider, `127.0.0.1` bind, Flask debug off, remote Ollama
  rejected, durable memory off, sensory retention rejected, microphone/camera
  off, and a 3600-second in-process idle TTL.
- Added `CARTER_SESSION_COOKIE_SECURE`; it remains `false` for the loopback HTTP
  quick start and must be set to `true` behind operator-configured HTTPS.
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

Historical 2026-07-25 result on Windows, Python 3.12.4, pytest 8.3.4,
pytest-cov 6.3.0:

| Metric | Result |
| --- | ---: |
| Tests collected | 172 |
| Passed | 172 |
| Failed | 0 |
| Skipped | 0 |
| Source statements | 13,378 |
| Branch-aware coverage | 32% |

The coverage value includes the large 17,000-line MCM module rather than
excluding it to inflate the result. That module has 16% line coverage in this
suite, which is a material residual validation risk and does not establish
semantic correctness across its possible engineering uses. No standard test
used the network, provider credentials, paid APIs, a microphone, camera
hardware, or model weights.

After the 2026-07-27 documentation-only reconciliation, the full offline suite
was rerun: all 172 tests passed again with no failures or skips. Runtime and
test files were unchanged by that reconciliation; the coverage figures above
remain from the 2026-07-25 branch-aware run.

Pre-reconciliation public-baseline verification on 2026-07-29 supersedes those
counts without erasing them:

| Metric | July 29 baseline result |
| --- | ---: |
| Tests collected | 226 |
| Passed | 226 |
| Failed | 0 |
| Overall branch-aware coverage | 35% |
| MCM coverage | 20% |
| Web-boundary coverage | 83% |

Security remediation PRs #3 and #4 were merged normally. CodeQL automatically
marked alerts #1 through #7 fixed; none was dismissed. Full Python SARIF for
that baseline contained zero results. At that verification point, open CodeQL,
secret-scanning, and Dependabot vulnerability alert counts were zero. The two
routine Dependabot PRs remained outside `main` and were not release blockers
absent new evidence.

Additional verification completed for the candidate and reverified for the
July 29 public baseline where applicable:

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
- project-scoped `pip-audit` resolution: no known vulnerabilities in the
  dependencies declared by the local project;
- baseline-aware detect-secrets, direct credential/path/artifact searches,
  Ruff, both Bandit scans, strict project dependency auditing, source and wheel
  builds, installed-wheel smoke, evidence reproduction, and all GitHub
  workflows passed on the verified pre-reconciliation baseline;
- all 18 engineering-pack files remain present and unchanged;
- staged-candidate verification: before creation of the release-candidate
  commit, verification was completed for 40 changed paths in a 193-file indexed
  tree; its complete cached diff was inspected; the baseline-aware
  `detect-secrets-hook` passed without mutating `.secrets.baseline`; and all
  other staged technical checks passed. Exact-commit and release-artifact
  verification was required after commit creation, with the results recorded
  without modifying the exact commit being verified. At the time this record
  was prepared, B-01 through B-08 and all applicable human publication gates
  remained open.

The machine-wide Python environment is not a release environment: `pip check`
reports unrelated pre-existing package conflicts, and a machine-wide
`pip-audit --strict` stops at the non-PyPI `en-core-web-lg` distribution. Those
results do not invalidate the clean project-scoped audit, but they also do not
qualify an exact locked release environment.

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

On July 28, 2026, Michael D. Lewis accepted the documented technical
dependency-license review for this Initial Public Research Release. No
dependency source is bundled or vendored in the wheel. This owner acceptance is
not a legal opinion, and future dependency resolutions and rebuilt artifacts
must be re-audited.

## Release-Owner Decisions

Michael D. Lewis recorded on July 28, 2026 that he is the sole human developer
and release owner, authorizes distribution under `AGPL-3.0-only`, and knows of
no employer, client, collaborator, contractor, unauthorized third-party
material, or other right restricting this release. He directed, selected,
integrated, modified, tested, organized, and approved the included work using
AI systems as development tools. AI assistance remains disclosed; no claim is
made that every AI-generated element independently qualifies for copyright
protection.

He knowingly chose public disclosure without obtaining patent review first and
accepts its possible effect on patent options. This records no conclusion about
whether any material is patentable.

He reviewed and approved the 18 engineering packs and recorded that they were
not knowingly copied or adapted from paid standards, proprietary manuals,
employer/customer procedures, protected tables, controlled-source examples, or
other unauthorized third-party material.

He approved `docs/PGM.md`, the privacy and exclusion findings, intentional
publication of his name, business identity, and Git author email, the 32%
overall and 16% MCM coverage values, the lack of independent professional
validation, disabled ChromaDB, optional integration limitations, and exact
verification evidence for `7acd4c4`. Those coverage values remain the
historical snapshot he accepted; the July 29 baseline verification recorded
35% overall, 20% MCM, and 83% for the web boundary.

## Known Limitations And Remaining Gate

- B-01 through B-07 have recorded release-owner dispositions in
  `RELEASE_BLOCKERS.md`.
- The three excluded legacy screenshots displayed two genuine session bearer
  tokens. Committed lifecycle evidence shows random, process-local, in-memory
  sessions with 24-hour expiration. Because the screenshots entered the legacy
  repositories on June 25, 2026, those sessions expired by June 26, 2026 at the
  latest under the committed implementation; a restart also invalidated them.
  No role password or evidence of unauthorized use was found. Present validity
  is reasonably excluded, without claiming misuse was impossible. Screenshot
  replacement/removal remains separate repository hygiene.
- Tested, monitored security, privacy, and trademark/branding contacts are now
  published in the applicable policy files.
- The approval-record commits and the pre-reconciliation public baseline
  received exact verification. The eventual merge commit for this documentation
  reconciliation and rebuilt release artifacts must be verified in the same
  manner before a tag or GitHub release.
- Chroma-backed persistence is unavailable pending an audited fixed release.
- The mock provider proves pipeline behavior only; it is not a language model
  or quality benchmark.
- EAS/MCM and packs are not professionally, regulatorily, or production
  validated. MCM coverage was 16% in the July 25 snapshot and is 20% in the
  July 29 pre-reconciliation baseline suite. Every result requires qualified
  independent review.
- SIS cannot establish novelty, patentability, feasibility, safety, or
  experimental validity.
- CSC camera support is local preview only; durable sensory retention is not
  implemented; optional provider/hardware behavior is not certified.
- The Flask server is a research/development runtime, not a production identity
  or high-availability platform.
- The maintained Carter deployment is authentication-protected, but this
  public research runtime has no user-authentication implementation. Its signed
  anonymous session ownership and CSRF controls are not proof of real-world
  identity, account isolation, or production authorization.
- The current private PGM's emergency-claim and tool-action guidance is
  model-facing prompt governance. It does not make emergency assertions
  verified facts or replace host authorization and tool controls.

The maintained lists are `KNOWN_LIMITATIONS.md`, `docs/LIMITATIONS.md`, and
`RELEASE_BLOCKERS.md`.

## Remaining Release Sequence

1. Merge the documentation reconciliation only under separate authorization.
2. From that exact merge commit, rerun tests, coverage, evidence, Ruff, Bandit,
   detect-secrets, history/path/artifact searches, dependency audit, source and
   wheel builds, installed-wheel smoke, pack verification, and the
   public/private PGM boundary check.
3. Rebuild controlled release artifacts and record the exact commit, tree,
   parents, artifact hashes, and results externally without modifying the
   verified commit.
4. Verify GitHub workflows and security scans on that exact public commit.
5. Obtain separate authorization before creating `v0.1.0` or a GitHub release.

The canonical source repository, public visibility, initial push, and baseline
CI verification are complete. As of this reconciliation, no `v0.1.0` tag or
GitHub release had been created; this PR creates or authorizes neither.
