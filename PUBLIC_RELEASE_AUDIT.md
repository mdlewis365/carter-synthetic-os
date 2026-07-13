<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Public Release Audit

Audit date: 2026-07-13

Project: Carter Synthetic OS

Target version: 0.1.0, Initial Public Research Release

License target: GNU Affero General Public License v3.0 only (AGPL-3.0-only)

## Scope And Repository Boundaries

This audit was completed before implementation files were copied into the
public repository.

| Role | Audited source | Treatment |
| --- | --- | --- |
| Private source | Private Carter production repository supplied locally for audit | Read-only audit source. Its Git history and working tree are not copied or modified. |
| Public destination | New `carter-synthetic-os` worktree | Clean independent Git repository on `release/carter-agpl-public`. |
| SOS documentation | `synthetic-operating-system` documentation repository | Read-only migration input. |
| EAS documentation | `engineering-assistance-system` documentation repository | Read-only migration input. |
| SIS documentation | `synthetic-ideation-system` documentation repository | Read-only migration input. |

Machine-specific absolute paths were used only in the local audit session and
are intentionally omitted from this public record.

The three older documentation repositories are BSD-3-Clause publications.
Their existing grants remain effective. Their documentation-only and private
implementation notices are not suitable for this release and will be
rewritten. This release requires explicit owner confirmation that the
first-party material may also be released under AGPL-3.0-only.

## Audit Method

The source was inspected with PowerShell 5.1.26100.8737, Git
2.51.0.windows.1, ripgrep 15.1.0, Python 3.12.4, and PyPDF2 3.0.1.
Read-only work included:

- complete tracked and untracked path inventories;
- route, import, function, storage, provider, and environment-variable searches;
- credential and privacy pattern searches over the working tree and all 39 commits;
- image inspection and in-memory PDF text inspection;
- local package metadata and installed-license inspection;
- manual review of entry points, subsystem modules, templates, browser code,
  tests, public snippets, packs, and existing documentation.

No private source file or private Git metadata was changed.

## System Inventory

### Carter Core And Flask Runtime

| Source | Role | Classification | Public action |
| --- | --- | --- | --- |
| carterServe.py | Primary Flask runtime, Carter orchestration, providers, jobs, uploads, authentication, SSE, EAS/SIS/CSC routes | First-party but security- and privacy-sensitive | Do not copy wholesale. Reimplement the same public boundaries with lazy providers, session ownership, no query tokens, no raw persistence, safe defaults, and explicit retention controls. |
| app.py | Legacy Flask/chat entry point with debug behavior | First-party but security-sensitive | Exclude; replace with packaged application factory and CLI. |
| carterServe - Copy.py | Legacy duplicate with weak fallback password | Not relevant duplicate and security-sensitive | Exclude. |
| Backup/carterServe.py | Backup of production runtime | Not relevant duplicate and security-sensitive | Exclude. |
| templates/index.html | Carter interface | First-party but security-sensitive | Use only as design/behavior reference; create sanitized public interface. |
| templates/index - Copy.html | Duplicate interface | Not relevant duplicate | Exclude. |
| static/index.js, static/index_styles.css | Carter browser client | First-party but security-sensitive | Rework for session-bound CSRF headers, local mock startup, and legal notices. |
| tests/test_carter_hardening_helpers.py | Carter hardening regression tests | First-party and releasable after fixture review | Migrate behavior into public tests with unmistakably synthetic fixtures. |

The production Carter runtime provides model selection, context construction,
job ownership, response streaming, and subsystem routes. It also mixes those
roles with private prompts, persistent job payloads, query-string tokens,
browser local-storage tokens, global conversation state, and eager provider
clients. A direct copy would not satisfy the release safety requirements.

### Synthetic Operating System

| Subsystem | Source paths | Observed implementation | Classification and action |
| --- | --- | --- | --- |
| Orchestration | carterServe.py; SynCogOS_PGM.py | Multi-stage governed prompt assembly and model execution | PGM is privacy-sensitive because it contains personal identity anchors and anthropomorphic claims. Publish a sanitized structured orchestration implementation. |
| AMS | SynCogOS_AMS.py; external ams_database and persistence paths | PostgreSQL conversation records, ChromaDB vectors, Ollama embeddings, spaCy processing, seeded memories | First-party but privacy-sensitive. Exclude all stores and seeds; publish storage interfaces plus empty in-memory/SQLite and optional Chroma adapters. |
| CRM | Synthetic_OS_CRM.py; external CRM_Data | Filesystem JSON rolling conversation and recovery storage | First-party but privacy-sensitive. Exclude data and machine paths; publish session-scoped bounded memory with retention off by default. |
| DIM | No active module found | No defensible active DIM implementation | Document as a public deterministic ingestion/deduplication interface. Do not claim the private tree contained an active DIM. |
| RAG | SynCogOS_RAG.py | ChromaDB knowledge retrieval, Ollama embeddings, spaCy | First-party but privacy-sensitive. Publish an optional adapter only; no persistence or model data. |
| LCM / OpRep | SynCogOS_LCM.py; reporting code in Carter/EAS | Raw conversation logging and operational-report terminology; one absolute machine path | First-party but privacy-sensitive. Replace with metadata-only event and OpRep generation; raw-content logging disabled by default. |
| Governance | SynCogOS_PGM.py; Engineering_Governance_Gate.py; public_snippets/synthetic_operating_system | Context governance and bounded gate contracts | Governance gate and sanitized contracts are releasable. Private identity/prompt text is excluded. |
| Deterministic computation / MCM | Synthetic_OS_MCM.py | Safe AST evaluation, schema repair, unit algebra, constraints, screening/selection, sensitivity, and run-health summaries | First-party and releasable, subject to owner signoff and final scan. Preserve as the main deterministic implementation. |
| SAL | Mentioned as a future boundary; no standalone active module | No defensible active SAL implementation in the private tree | Implement and label a bounded public semantic-adjudication layer; do not imply the private version was complete. |
| Temporal/context anchoring | SynCogOS_PGM.py | Time, conversation, AMS, and RAG context assembly | Publish generic explicit anchors; exclude identity and memory content. |
| Tool boundaries | carterServe.py; public_snippets/synthetic_operating_system/tool_invocation_boundary.py | Provider/file/tool execution boundaries | Publish allowlisted, redacted public boundary. |
| Observability | carterServe.py; SynCogOS_LCM.py; public_snippets/synthetic_operating_system/log_event_schema.py | Jobs, logs, redacted event schema | Publish metadata-only events; exclude production jobs/logs. |

The public_snippets/synthetic_operating_system directory contains 9
sanitized/adapted reference files for memory schemas, retrieval, context,
governance, registry, events, tools, and recovery. They are first-party and
releasable, but are not by themselves a complete runtime.

### Engineering Assistance System

| Source paths | Observed implementation | Classification and action |
| --- | --- | --- |
| Engineering_Decision_Record.py | Defensive EDR construction, validation, compaction, and summaries | First-party and releasable. |
| Engineering_Governance_Gate.py | Deterministic risk, computation, diagnostic, selection, human-review, and report classification | First-party and releasable. |
| Synthetic_OS_MCM.py | Deterministic computation and sensitivity | First-party and releasable. |
| carterServe.py EAS functions and routes | Mode normalization, two-stage provider workflow, pack routing, schema recovery, MCM execution, evidence maps, report sanitation, SSE | First-party but security-sensitive as embedded in production runtime. Publish sanitized modular equivalents. |
| engineering_packs/README.md | Pack format and registry documentation | First-party and releasable. |
| engineering_packs/core_release_pack.md | Core release checks | First-party and releasable subject to owner/IP review. |
| engineering_packs/core_release_assessment_pack.md | Core assessment checks | First-party and releasable subject to owner/IP review. |
| engineering_packs/aerospace_aerodynamics_pack.md | Aerodynamics guidance | First-party and releasable subject to owner/IP review. |
| engineering_packs/fluid_pump_loop_pack.md | Pump-loop guidance | First-party and releasable subject to owner/IP review. |
| engineering_packs/mechanical_power_transmission_pack.md | Power-transmission guidance | First-party and releasable subject to owner/IP review. |
| engineering_packs/structural_mechanical_bracket_pack.md | Structural bracket guidance | First-party and releasable subject to owner/IP review. |
| engineering_packs/thermal_enclosure_cooling_pack.md | Thermal enclosure guidance | First-party and releasable subject to owner/IP review. |
| engineering_packs/domains/*.md (5 files) | Aerospace, pneumatics, DC controls, exhaust airflow, software systems domain packs | First-party and releasable subject to owner/IP review. |
| engineering_packs/modes/*.md (5 files) | Solve, diagnose, review, improve, and explore mode packs | First-party and releasable subject to owner/IP review. |
| templates/eas.html, templates/eas_v1.html | EAS interfaces | First-party but security-sensitive | Replace with one sanitized public interface. |
| static/eas.js, static/eas_v1.js, static/eas_styles.css | EAS browser workflows | First-party but security-sensitive | Use as behavior reference only. |
| tests/test_eas_*.py, tests/test_engineering_*.py, tests/test_mcm_*.py, and pack tests | 456-test-suite concentration on EAS/MCM behavior | First-party and generally releasable after fixture provenance review. Create public synthetic coverage rather than copying private operational references. |

The EAS_v1_Test directory has 127 tracked artifacts, including generated
reports and unlabeled TXT/CSV inputs. None is clearly labeled synthetic.
The entire directory is ownership/privacy unclear and is excluded pending
individual human review.

### Synthetic Ideation System

| Source | Role | Classification and action |
| --- | --- | --- |
| Synthetic_IS_MPM.py | Prompt construction for mechanism, architecture, process, algorithmic, and hybrid modes | First-party but prompt/IP-sensitive. Publish a provider-neutral structured workflow rather than private prompt text. |
| SIS_InventionGates.py | NPAM/IVA/CIT deterministic heuristics | First-party and technically releasable, but header records an assistant draft. Human authorship/ownership review is required. Publish only cleared logic. |
| Synthetic_IS_PAC.py | Docstring-only placeholder | Not an implemented prior-art module | Exclude and document the limitation. |
| sisVectorTemplates.txt | Ideation templates | Ownership unclear and patent/prompt-sensitive | Exclude pending authorship and IP review. |
| templates/sis.html; static/sis.js; static/sis_styles.css | SIS interface and client | First-party but security-sensitive | Replace with sanitized public workflow. |
| docs/invention_modes.md, docs/scientist_input_module.md, docs/SIS_architecture_overview.md, docs/workflow_example.md | First-party subsystem documentation | Releasable as rewrite input. |
| public_snippets/synthetic_ideation_system/*.py (8 files) | Schemas, modes, evaluator aggregation, rejection checks, scoring, workflow state, invariant validation | First-party, sanitized, and releasable; extend into a runnable public workflow. |

The live private SIS route does not call the MCM or the NPAM/IVA/CIT module.
The public release must not claim those private integrations already existed.
The new public integration will be identified as a 0.1.0 architecture change.
All generated concepts are hypotheses requiring independent validation,
prior-art and patent review, safety assessment, and experimental confirmation.

### Carter Sensory Console

| Source | Role | Classification and action |
| --- | --- | --- |
| carter_ears.py | Hearing state, wake-name classification, transcript rolling buffer | First-party but privacy/security-sensitive. Migrate with all state session-scoped. |
| sensory_transcription.py | In-memory Gemini audio transcription boundary | First-party but privacy/security-sensitive. Rename configuration, keep lazy optional import, and disclose cloud transfer. |
| sensory_interpretation.py | Local Ollama JSON interpretation and session-keyed latest state | First-party but security-sensitive. Restrict defaults to loopback and normalize output. |
| sensory_voice.py | Configurable ElevenLabs TTS and playback isolation | First-party but security-sensitive. Use uppercase environment variables and never include a voice ID or audio. |
| templates/sensory.html | CSC interface | First-party but security-sensitive. Rebuild with explicit microphone/camera action and clear active indicators. |
| static/sensory.js; static/sensory_styles.css | Browser WAV conversion, MediaRecorder fallback, voice orb, token handling | First-party but security-sensitive. Preserve public-safe capture/WAV concepts; remove local-storage auth tokens. |
| tests/test_sensory_*.py | Authorization, session isolation, wake-name, no persistence, JSON normalization, failures | First-party and releasable using synthetic fixtures. |

No camera implementation exists in the private tree. The public interface may
offer an explicit local preview boundary, disabled by default, but must not
claim server-side camera interpretation. Microphone and camera retention are
disabled by default; raw audio, images, cloned voice assets, and identifiers
are excluded.

### Providers, Storage, And External Services

| Integration | Private implementation | Release treatment |
| --- | --- | --- |
| Mock | None | Add a clearly labeled deterministic synthetic provider as the default. |
| Ollama | Direct SDK and HTTP usage; local embeddings and generation | Optional lazy provider with 127.0.0.1 default; do not distribute weights. |
| OpenAI | Eager SDK/client imports and file/model calls | Optional lazy provider configured only by environment. |
| Anthropic | Eager client construction requiring a key | Optional lazy provider configured only by environment. |
| Google Gemini | SDK generation, uploads, CSC transcription | Optional lazy provider configured only by environment; document when audio is sent. |
| ElevenLabs | TTS SDK/HTTP | Optional lazy provider; key and voice ID supplied by operator. |
| ChromaDB | AMS/RAG persistence | Optional lazy adapter; no persistence directory copied. |
| PostgreSQL/psycopg | AMS conversation store | Not required for public demo; legacy adapter omitted from core pending license/operations review. |
| SQLite | No private integration found | Add an empty, opt-in local public memory adapter; do not claim it was migrated. |
| Flask/SSE | Primary server and streamed job events | Preserve through a factory, CSRF/session checks, and in-memory jobs. |

## Ownership Classification Summary

### First-Party And Releasable

- Synthetic_OS_MCM.py.
- Engineering_Decision_Record.py.
- Engineering_Governance_Gate.py.
- engineering_packs/**/*.md, subject to final owner and IP confirmation.
- public_snippets/**/*.py and their READMEs.
- most public-facing Markdown documentation after claims review.
- SIS_InventionGates.py only after assistant-draft authorship review.
- synthetic tests whose provenance is confirmed and whose fixtures contain no
  production references.

### First-Party But Security-Sensitive

- carterServe.py, app.py, provider initialization, authentication, uploads,
  job access, SSE, and persistence code.
- all interactive templates and browser JavaScript.
- CSC Python boundaries.
- SynCogOS_AMS.py and SynCogOS_RAG.py configuration and initialization.

These files are used as read-only architecture/behavior inputs. Public
replacements are deliberately modular and default-deny.

### First-Party But Privacy-Sensitive

- SynCogOS_PGM.py identity/context content.
- Synthetic_OS_CRM.py conversation files.
- SynCogOS_LCM.py raw logs.
- job_store/** and external memory/persistence directories.
- screenshots containing actual responses or operational state.

### Generated Artifacts

- job_store/**.
- EAS_v1_Test/** generated PDFs.
- root Carter Output 03282026*.pdf.
- __pycache__/**, tests/__pycache__/**, .pytest_cache/**.
- interrupted patch files and temporary job artifacts.

### Configuration Containing Secrets

No literal credential file was found. Production code consumes authentication,
database, OpenAI, Anthropic, Google, ElevenLabs, Ollama, and persistence
variables. Only variable names and empty placeholders may be migrated. A new
.env.example will contain no operational value.

### Third-Party Code

No vendored third-party Python source was identified. Imported packages remain
external dependencies. MathJax is loaded from a floating CDN version and is
not migrated. An inline caret SVG has unresolved provenance and is not copied.

### Third-Party Assets Or Ownership Unclear

- static/favicon.ico.
- embedded notification/no-sleep media.
- all existing root and assets/*.png images.
- AI_Systems_thumbnail.png.
- AsyncGenAIArchitecture12292025.png.
- LaTex_display_03212026.png.
- sisVectorTemplates.txt.
- EAS_v1_Test/** inputs and generated reports.

No model weights, font files, or raw audio recordings were found. External
model weights remain separately obtained and separately licensed.

### Not Relevant To The Public Release

- private .git/** history and metadata;
- .agents/** and .codex/**;
- backups and duplicate copies;
- local caches, temporary files, interrupted patches, and deployment state;
- production-only login capture and tunnel/deployment configuration.

## Secret And Privacy Findings

The detailed findings and commands are recorded in SECURITY_RELEASE_AUDIT.md.
Release-critical findings from this pre-copy audit are:

1. assets/eas_screenshot.png and assets/sis_screenshot_a.png plus
   assets/sis_screenshot_b.png visibly contain production URL query
   authentication/session tokens. They are excluded. The tokens must be
   revoked or their expiry confirmed, and the older public documentation
   repository histories must be reviewed.
2. assets/Backend_Carter_working.png exposes private operational logs,
   provider activity, timestamps, and memory/runtime details. It is excluded.
3. carter_web_home_page_b_12292025.png and
   carter_web_home_page_c_12292025.png contain memory-backed output and
   personal context. All root UI screenshots are excluded.
4. job_store/** contains 212 JSON records and temporary artifacts totaling
   about 31 MB, including prompts, outputs, owner identifiers, reports, and a
   possible phone-number pattern. It is excluded in full.
5. email_addresses.txt contains 167 addresses. It is excluded.
6. The private .gitignore is UTF-16 LE and is not honored by Git. It is not
   copied; a UTF-8 public ignore file will be verified.
7. No high-confidence literal provider key, private-key header, JWT,
   URL-embedded text credential, or secret assignment was found in the source
   working tree or its 39 commits. Raster-image findings demonstrate why text
   scanning alone is insufficient.

No known active credential will be copied into the public repository.

## Dependency And License Audit Summary

The private requirements file declares Flask 3.0.3, gunicorn 22.0.0,
waitress 3.0.0, elevenlabs 2.9.2, and google-genai 1.57.0. The code also
directly imports Flask-Cors, ollama, tzlocal, pytz, chromadb, psycopg,
colorama, spaCy, openai, and anthropic without declaring all of them.

Installed metadata is evidence, not a compatibility determination. Initial
observations are:

| Dependency | Local evidence | Audit status |
| --- | --- | --- |
| Flask 3.0.3 | BSD classifier | Exact license text to verify. |
| Werkzeug 3.1.4 | BSD-3-Clause expression | Human review required. |
| waitress 3.0.0 | ZPL-2.1 metadata/license | Compatibility and notice review required. |
| gunicorn 22.0.0 | Not installed/cached | Unresolved. |
| elevenlabs 2.9.2 | MIT metadata | No obvious conflict; verify source. |
| google-genai 1.57.0 | Apache-2.0 expression | No obvious conflict; verify notices. |
| Flask-Cors 6.0.2 | MIT expression | No obvious conflict. |
| ollama 0.6.1 | MIT expression/license | Model licenses remain separate. |
| chromadb 1.4.0 | Apache license classifier/text | Optional; human review required. |
| psycopg 3.1.19 | LGPLv3 metadata/text | Obligations review required. |
| spaCy 3.8.11 | MIT metadata | Model and training-data rights are separate. |
| en-core-web-sm 3.8.0 | MIT package; OntoNotes training-data notice | Do not vendor pending model/data review. |
| openai 2.15.0 | Apache-2.0 metadata | Optional; verify source. |
| anthropic 0.85.0 | MIT metadata | Optional; verify source. |
| pytest 8.3.4 | MIT metadata | Development/test only. |

The final direct dependency set will be smaller than the private environment.
Every cloud, local-model, persistence, and sensory SDK will be an optional
extra. LICENSE_COMPATIBILITY_REPORT.md and THIRD_PARTY_NOTICES.md will carry
the final evidence and unresolved legal questions. This audit is not legal
advice.

## Migration Decisions

- Preserve the full cleared deterministic MCM implementation and cleared EAS
  decision/governance modules.
- Preserve cleared first-party engineering packs.
- Extend the sanitized SOS/EAS/SIS public contracts into runnable workflows.
- Replace the mixed production Flask monolith with a package factory and
  explicit subsystem interfaces.
- Use a deterministic mock provider and synthetic fixtures by default.
- Make Ollama and cloud providers lazy, optional, and failure-tolerant.
- Keep memory and sensory retention disabled by default.
- Store no raw prompt/response in normal operational events.
- Require explicit browser action for microphone and camera permissions.
- Regenerate any future screenshot from mock/local synthetic data.
- Document every omission in EXCLUSIONS.md and every material architecture
  change in PUBLIC_RELEASE_REPORT.md.

## Pre-Implementation Release Blockers

| Blocker | Effect on local preparation | Required human action |
| --- | --- | --- |
| Screenshot-exposed production tokens | Images cannot be released; possible account/session exposure remains outside this new repository | Revoke/expire tokens and audit older public Git history. |
| First-party ownership and patent review | Code can be prepared locally but must not be made public | Confirm ownership, employer/contract rights, and patent strategy. |
| SIS assistant-draft header and vector templates | Uncleared SIS material cannot be copied verbatim | Confirm authorship and redistribution rights. |
| Engineering pack provenance | Packs can be staged locally, but public release awaits signoff | Confirm first-party authorship and no controlled/proprietary source material. |
| Dependency license questions | Optional dependency set may change | Review ZPL, LGPL, model/data, gunicorn, and notice obligations. |
| Prior BSD documentation releases | New text must not imply prior grants were withdrawn | Approve dual/relicensing explanation and migration language. |
| No active DIM/SAL/camera implementation in private tree | Claims must be bounded | Review new 0.1.0 public implementations and status labels. |

Local preparation may continue, but no push, visibility change, tag, or release
is authorized until PUBLIC_PUSH_CHECKLIST.md is completed by a human reviewer.
