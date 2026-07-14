<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Public Release Exclusions

Audit date: 2026-07-13

This is the exclusion ledger for Carter Synthetic OS 0.1.0. Paths are relative
to the audited private source repository. A glob row covers every matching
file; grouped private records are intentionally not named individually when a
filename could disclose a user, request, timestamp, or operational detail.

"Replacement" means a clean public implementation or synthetic fixture was
created. It does not mean the excluded bytes were copied and edited. No secret
value, private identifier, absolute local path, or private record content is
reproduced here.

## Repository, Configuration, And Deployment State

| Original relative path or group | Count | Category | Exclusion reason | Sanitized replacement | Runtime effect |
| --- | ---: | --- | --- | --- | --- |
| `.git/**` | 39 commits plus metadata | Private repository/history | Independent public history is mandatory; private history may contain deleted or operational material. | Yes: new independent repository and release branch. | None for public runtime; provenance history is intentionally absent. |
| `.agents/**`, `.codex/**` | All matching files | Local tooling state / not release material | Machine- and session-specific agent state has no product-runtime role. | No. | None. |
| Private `.gitignore` | 1 | Configuration artifact | UTF-16 LE file was not honored by Git and was unsuitable as a public safeguard. | Yes: reviewed UTF-8 `.gitignore`. | None; public hygiene is improved. |
| `.env`, `.env.*` other than an empty example, credential exports, local provider configuration | All matching files if present | Configuration containing secrets | Operational values, account IDs, URLs, paths, and keys cannot enter public history. | Yes: placeholder-only `.env.example`. | Operators must provide their own optional-provider values. |
| Cloudflare/tunnel files, production-domain configuration, production login/session captures | All matching files if present | Production-infrastructure risk | Could expose routing, authentication, origin, or deployment details. | No; deployment docs use loopback-safe examples. | Production deployment is intentionally not reproduced. |
| Private caches, crash dumps, interrupted patch files, temporary files, local logs, upload directories | All matching files | Generated artifact / operational data | May contain prompts, responses, paths, tokens, or user content and is not source. | No; public ignores block these classes. | None for clean startup. |

## Carter And Web Runtime Rewrites

| Original relative path or group | Count | Category | Exclusion reason | Sanitized replacement | Runtime effect |
| --- | ---: | --- | --- | --- | --- |
| `carterServe.py` | 1 | First-party, security- and privacy-sensitive | Production monolith mixes orchestration with private prompts, global state, persistence, query tokens, jobs, providers, uploads, auth, and deployment behavior. It was not safe to copy wholesale. | Yes: modular `src/carter`, `src/sos`, `src/eas`, `src/sis`, and `src/csc` implementation. | Public workflows are real, but production integrations and private state are absent. |
| `app.py` | 1 | First-party, security-sensitive | Legacy entry point includes unsuitable debug/startup behavior. | Yes: packaged application factory and CLI with loopback/default-debug-off policy. | Command and configuration surface changed. |
| `carterServe - Copy.py`, `Backup/carterServe.py` | 2 | Duplicate/backup, security-sensitive | Stale copies increase ambiguity and preserve unsafe legacy behavior. | Covered by the modular public runtime. | None. |
| `templates/index.html`, `templates/index - Copy.html` | 2 | First-party, security-sensitive | Legacy UI participates in unsafe token/state patterns and contains private-deployment assumptions. | Yes: clean Carter interface with legal/source notices. | Appearance and request flow changed; core public workflow remains. |
| `templates/eas.html`, `templates/eas_v1.html` | 2 | First-party, security-sensitive | Duplicate legacy interfaces are coupled to production endpoints and state. | Yes: one public EAS interface. | Legacy UI variants are not preserved. |
| `templates/sis.html` | 1 | First-party, security-sensitive | Coupled to private SIS prompt and route behavior. | Yes: sanitized governed SIS workflow. | Exact legacy prompt/UI behavior is absent. |
| `templates/sensory.html` | 1 | First-party, privacy- and security-sensitive | Legacy capture UI did not meet explicit-action, global-state, and session-retention release requirements. | Yes: CSC interface with explicit microphone/camera/TTS controls. | Capture behavior is safer and intentionally session-scoped. |
| `static/index.js`, `static/index_styles.css` | 2 | First-party, security-sensitive | Legacy token handling and production assumptions were not suitable for release. | Yes: packaged public client and styling. | Browser protocol changed to session-bound CSRF requests. |
| `static/eas.js`, `static/eas_v1.js`, `static/eas_styles.css` | 3 | First-party, security-sensitive | Legacy scripts are tied to private route/job behavior and duplicate interfaces. | Yes: one sanitized EAS browser flow. | Legacy variants are absent. |
| `static/sis.js`, `static/sis_styles.css` | 2 | First-party, security-sensitive | Private prompt/route coupling and unclear output handling. | Yes: sanitized SIS client. | Exact private workflow is not reproduced. |
| `static/sensory.js`, `static/sensory_styles.css` | 2 | First-party, privacy- and security-sensitive | Legacy capture/token behavior was used only as a behavioral reference. | Yes: explicit raw-WAV capture, scoped state, indicators, and cleanup. | No retained production sensory behavior or data. |

## SOS Memory, Context, Reporting, And Providers

| Original relative path or group | Count | Category | Exclusion reason | Sanitized replacement | Runtime effect |
| --- | ---: | --- | --- | --- | --- |
| `SynCogOS_PGM.py` | 1 | First-party, privacy- and prompt-sensitive | Contains personal identity anchors, private contextual text, and anthropomorphic claims unsuitable for a defensible public release. | Yes: provider-neutral structured orchestration, generic identity/continuity rules, and explicit anchors. | Private Carter identity content is absent. |
| `SynCogOS_AMS.py` | 1 | First-party, privacy- and operations-sensitive | Initializes seeded memories, PostgreSQL records, Chroma vectors, embeddings, and machine-specific persistence. | Yes: empty session-scoped memory interfaces plus safe adapters. | Existing long-term memories and production persistence are unavailable. |
| `Synthetic_OS_CRM.py` | 1 | First-party, privacy-sensitive | Filesystem rolling conversations and recovery data may contain user content and local paths. | Yes: bounded in-memory session CRM with idle expiry. | Conversations do not survive restart by default. |
| `SynCogOS_RAG.py` | 1 | First-party, privacy- and dependency-sensitive | Couples private knowledge stores to Chroma, embeddings, and local model/data assets. | Yes: source-visible optional boundary without bundled persistence or model data. | Public 0.1.0 does not declare ChromaDB; persistent RAG is unavailable by default. |
| `SynCogOS_LCM.py` | 1 | First-party, privacy-sensitive | Raw conversation logging and an absolute local path could expose prompts, responses, and operations. | Yes: metadata-only operational events with raw content disabled. | Raw legacy logs and full OpRep transcripts are unavailable. |
| Private AMS, CRM, RAG, LCM, PostgreSQL, SQLite, and Chroma persistence directories or databases | All matching stores | Private data / generated artifact | May contain memories, conversations, embeddings, identifiers, prompts, or operational records. | Yes: empty stores and synthetic fixtures only. | No continuity with the production instance. |
| `job_store/**` | 212 JSON records plus temporary artifacts, about 31 MB | Generated artifact / private operational data | Contains prompts, outputs, owner identifiers, reports, and a possible phone-number pattern. Individual filenames are withheld to avoid further disclosure. | Yes: bounded in-memory public jobs and synthetic evidence. | Production jobs cannot be resumed or inspected. |
| `email_addresses.txt` | 1 file, 167 addresses | Personally identifiable information | Private address list has no place in source or test fixtures. | No. | None. |
| Production provider-account data, cached prompts/outputs, billing identifiers, model selections, service URLs, or voice IDs | All matching values/artifacts | Credential or private operational data | Operator-specific configuration and outputs may identify accounts or disclose data. | Yes: environment variable names and empty placeholders only. | Operators configure their own providers; mock mode remains runnable. |
| Local model weights, tokenizers, embedding models, and downloaded model data | All matching files if present | Third-party/model asset | Redistribution and training-data rights were not established; files are large and separately obtained. | No; Ollama HTTP boundary and install documentation only. | Local mode requires an operator-supplied service/model. |

## EAS Source, Packs, Tests, And Generated Material

| Original relative path or group | Count | Category | Exclusion reason | Sanitized replacement | Runtime effect |
| --- | ---: | --- | --- | --- | --- |
| EAS route/provider/prompt sections embedded in `carterServe.py` | 1 grouped source region | First-party, security-sensitive | Production auth, job, provider, and private prompt behavior cannot be separated safely by copying the monolith. | Yes: modular two-stage EAS workflow using cleared MCM, EDR, governance, and packs. | Endpoint shape changed; public deterministic workflow remains. |
| `EAS_v1_Test/**` | 127 tracked artifacts | Generated artifact / privacy and ownership unclear | Includes generated reports and unlabeled TXT/CSV inputs not clearly established as synthetic or redistributable. | Yes: small explicitly synthetic fixtures and reproducible evidence case. | Private regression corpus is absent; public coverage is narrower. |
| Private `tests/test_eas_*.py`, `tests/test_engineering_*.py`, `tests/test_mcm_*.py`, and pack tests | All matching private tests not independently selected | First-party but fixture provenance unconfirmed | Tests may encode private operational references or unclear inputs. They were not copied wholesale. | Yes: new synthetic unit/integration coverage for the public contracts. | The private suite's full breadth is not claimed. |
| `Carter Output 03282026*.pdf` | All matching root PDFs | Generated artifact / private output | Generated reports may contain user inputs, derived results, or operational metadata. | Yes: machine-generated synthetic evidence artifacts. | Historical reports are unavailable. |
| `LaTex_display/**`, `LaTex_display_03212026.png` | All matching files | Generated/third-party provenance unclear | Rendered equations/assets have unclear inputs and redistribution provenance. | No; browser output uses text/first-party formatting. | Exact legacy rendering assets are absent. |
| Other private PDF, TXT, CSV, and report fixtures outside cleared first-party source/packs | All matching uncleared artifacts | Generated artifact / ownership unclear | Inputs and outputs were not individually proven synthetic and redistributable. | Synthetic replacements where needed for tests. | Historical/private examples are absent. |

The 18 first-party engineering pack Markdown files were included rather than
excluded, but publication remains blocked on human authorship, IP, and
controlled-source review. No pack should be interpreted as reproducing a
licensed engineering standard.

## SIS Source And Draft Material

| Original relative path or group | Count | Category | Exclusion reason | Sanitized replacement | Runtime effect |
| --- | ---: | --- | --- | --- | --- |
| `Synthetic_IS_MPM.py` | 1 | First-party, prompt/IP-sensitive | Private mechanism, architecture, process, algorithmic, and hybrid prompt text was not cleared for verbatim release. | Yes: provider-neutral structured mode and evaluator workflow. | Exact private prompts are absent. |
| `SIS_InventionGates.py` | 1 | Ownership unclear | Header records an assistant draft; human authorship and redistribution review is unresolved. | Yes: only separately cleared public invariant/evaluation behavior is represented. | NPAM/IVA/CIT private implementation is not claimed as migrated. |
| `Synthetic_IS_PAC.py` | 1 | Placeholder / not implemented | Docstring-only prior-art component is not a real implementation and would misstate capability. | No; limitation is documented. | No automated prior-art search is provided. |
| `sisVectorTemplates.txt` | 1 | Ownership and patent/prompt sensitivity unclear | Authorship, provenance, and invention-disclosure implications require human review. | Yes: generic first-party public schemas and synthetic examples. | Legacy vector templates are unavailable. |
| Uncleared SIS draft prompts, vector material, generated concepts, and private example outputs | All matching files | Privacy/IP/ownership unclear | May contain confidential invention material or unreviewed generated authorship. | Synthetic examples only. | No private invention continuity or prior-art claim. |

## CSC, Recordings, And Sensory Data

| Original relative path or group | Count | Category | Exclusion reason | Sanitized replacement | Runtime effect |
| --- | ---: | --- | --- | --- | --- |
| Private `carter_ears.py`, `sensory_transcription.py`, `sensory_interpretation.py`, `sensory_voice.py` files as complete byte-for-byte sources | 4 | First-party, privacy- and security-sensitive | Provider setup, state, retention, and capture boundaries required session isolation and configuration hardening. | Yes: modular CSC hearing, interpretation, transcription, and configurable TTS boundaries. | Public defaults are retention-off and capture-off; private provider state is absent. |
| Private `tests/test_sensory_*.py` and sensory fixtures not independently selected | All matching private tests | First-party but fixture provenance unconfirmed | Could contain private payload shapes, tokens, audio, or operational assumptions. | Yes: unmistakably synthetic sensory/session tests. | Optional real-provider and hardware coverage is not included in standard tests. |
| Microphone recordings, WAV/audio uploads, transcription caches, cloned voice samples, playback files | All matching files if present | Biometric/private data or third-party asset | Consent, identity, provider, and redistribution risks; no recording is required for source review. | Synthetic in-memory bytes only in tests. | Users must explicitly capture their own session audio. |
| Camera images, browser recordings, video captures, or interpretation caches | All matching files if present | Private sensory data | No safe private camera implementation or releasable dataset exists. | Local browser preview boundary only; no server-side camera interpretation claim. | Camera analysis and retention are unavailable. |
| ElevenLabs voice identifiers, cloned voice metadata, and provider account identifiers | All matching values/artifacts | Credential/account/private voice data | Could identify a private voice or account and is operator-specific. | Empty environment placeholders and configurable provider boundary. | TTS requires operator configuration; no cloned voice is supplied. |

## Screenshots, Media, And Third-Party Assets

| Original relative path or group | Count | Category | Exclusion reason | Sanitized replacement | Runtime effect |
| --- | ---: | --- | --- | --- | --- |
| `assets/eas_screenshot.png`, `assets/sis_screenshot_a.png`, `assets/sis_screenshot_b.png` | 3 | Credential exposure / private screenshot | Display production query authentication/session tokens. | No. Any future image must be newly generated in mock mode. | None; documentation has no private screenshot. |
| `assets/Backend_Carter_working.png` | 1 | Private operational screenshot | Displays logs, provider activity, timestamps, memory, and runtime details. | No. | None. |
| `carter_web_home_page_b_12292025.png`, `carter_web_home_page_c_12292025.png` | 2 | Privacy-sensitive screenshot | Contains memory-backed output and personal context. | No. | None. |
| Other root UI screenshots and `assets/*.png` not listed above | All matching images | Ownership/privacy unclear | Visual review and provenance were insufficient for public redistribution; screenshots may expose contextual data missed by text scans. | Architecture diagrams are first-party Mermaid source; no private raster replacement. | Cosmetic only. |
| `AI_Systems_thumbnail.png`, `AsyncGenAIArchitecture12292025.png` | 2 | Ownership/third-party asset unclear | Redistribution provenance and embedded material were not established. | Yes: textual/Mermaid architecture documentation. | Cosmetic/documentation only. |
| `static/favicon.ico` | 1 | Third-party asset / ownership unclear | Original artwork provenance and redistribution rights were not established. | No. | Browser uses its default icon. |
| Embedded notification/no-sleep media and other audio/video UI assets | All matching files | Third-party/media asset | Provenance and redistribution terms are unclear; media is not needed for the demonstration. | No. | Optional cosmetic/notification behavior is absent. |
| Floating-CDN MathJax integration | 1 external integration | Third-party code/service | Floating remote code is not vendored or required; version, integrity, and redistribution terms were not pinned. | No; public UI does not require it. | Legacy equation rendering may differ. |
| Inline caret SVG from the legacy interface | 1 | Third-party asset / provenance unclear | Authorship and redistribution rights were not established. | Yes: standard text/CSS controls and licensed icon-free interface. | Cosmetic only. |
| Third-party fonts, images, datasets, model files, and audio not covered by an explicit redistribution grant | All matching files if present | Third-party asset | No assumption of AGPL compatibility or redistribution permission is made. | No. | Operators separately obtain optional services/models/assets. |

## Tests, Caches, And Miscellaneous Generated Files

| Original relative path or group | Count | Category | Exclusion reason | Sanitized replacement | Runtime effect |
| --- | ---: | --- | --- | --- | --- |
| Private test files and fixtures not expressly represented by new public synthetic tests | All unmatched private tests/fixtures | First-party or ownership unclear | Wholesale copying could migrate private payloads, paths, provider assumptions, or generated outputs. | Yes where required for public behavior; otherwise no. | Public test coverage is reported honestly and does not claim parity with the private suite. |
| `__pycache__/**`, `tests/__pycache__/**`, `.pytest_cache/**`, coverage files | All matching files | Generated artifact | Interpreter/test caches are not source and may embed paths. | No; regenerated locally and ignored. | None. |
| SQLite files, Chroma persistence, logs, recordings, uploaded files, generated user reports, crash dumps | All matching files | Generated/private artifact | May retain user content, prompts, identifiers, vectors, or machine data. | Empty runtime state and synthetic evidence only. | Persistent production state is intentionally absent. |
| Local virtual environments, installed packages, IDE settings, local models | All matching files | Generated/third-party/not release material | Machine-specific, large, and separately licensed. | Setup scripts and declared dependency metadata only. | Installation is required. |

## Functional Consequences

The exclusions do not turn the release into a documentation-only repository.
The public tree contains working first-party Carter, SOS, EAS, SIS, and CSC
implementations, a deterministic mock provider, tests, and reproducible
synthetic evidence. The exclusions deliberately remove production continuity:
no private memory, job, user, voice, model, provider account, report, recording,
or deployment can be recovered from this release.

Material limitations caused by exclusions are documented rather than hidden:
persistent Chroma-backed retrieval is not installable in 0.1.0; private
identity/prompts and historical reports are absent; prior-art search and
server-side camera interpretation are not implemented; provider and local
model behavior requires operator-supplied services; and the public synthetic
test corpus does not claim parity with private production validation.

No excluded file may be restored merely because it appears useful. Restoration
requires documented ownership, privacy, security, and dependency-license
review plus a fresh secret scan before the bytes enter Git history.
