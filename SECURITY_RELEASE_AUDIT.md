<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Security Release Audit

Initial audit date: 2026-07-13

Working-tree reverification dates: 2026-07-25 and 2026-07-27

Private-reference reconciliation date: 2026-07-27

Release candidate: Carter Synthetic OS 0.1.0, Initial Public Research Release

This report records the security and privacy checks performed while preparing
the clean public repository. It is a point-in-time release audit, not a
guarantee that the software is free of vulnerabilities or that excluded
credentials were never exposed elsewhere.

## 2026-07-29 Public-Main Supersession Notice

The dated preparation findings below are preserved, including the historical
172-test, 32% overall coverage, and 16% MCM coverage snapshots. Their
present-tense pre-push instructions describe the state in which they were
recorded and are operationally superseded by this notice.

The canonical repository is now public at
`https://github.com/mdlewis365/carter-synthetic-os`. The pre-reconciliation
public baseline, verified on July 29, 2026, was
`396deb6d5f2b86bde46c6d6ac4e18f448f4ed941`, with tree
`90bac4511fad02a71e6004e844e41a1230003067` and 193 tracked files.
`docs/PGM.md` is committed and public. The initial private push, public
visibility change, and subsequent CI verification were completed.

Security remediation PRs #3 and #4 were merged with normal merge commits.
CodeQL automatically marked alerts #1 through #7 fixed; none was dismissed.
At the July 29 baseline verification, open CodeQL, secret-scanning, and
Dependabot vulnerability alert counts were zero. That exact baseline passed 226
tests with 35% branch-aware overall coverage, 20% MCM coverage, and 83%
web-boundary coverage. Ruff, Bandit, baseline-aware detect-secrets, strict
project dependency auditing, source and wheel builds, installed-wheel smoke,
evidence reproduction, and GitHub workflows passed. All 18 engineering-pack
files were present and unchanged.

Release-owner decisions B-01 through B-07 were resolved or accepted. The
documented absence of independent professional validation and optional
provider, browser, hardware, and ChromaDB support remain research limitations,
not unresolved publication blockers. As of this reconciliation, no `v0.1.0`
tag or GitHub release had been created; this PR creates or authorizes neither.
Exact verification of the eventual documentation-merge commit and rebuilt
release artifacts remains required before separate tag and GitHub release
authorization.

## Repository Boundary

The private Carter repository was treated as read-only. Its `.git` directory,
history, operational state, memories, job data, screenshots, credentials, and
machine-specific configuration were not copied. Public implementation files
were selected or rewritten into an independently initialized repository on
`release/carter-agpl-public`.

Absolute local paths and suspicious values are intentionally omitted from this
report. Findings are described by category, count, and remediation so this
document cannot become another disclosure channel.

## Tools And Versions

| Stage | Tool | Version | Purpose |
| --- | --- | --- | --- |
| Private pre-copy audit | Windows PowerShell | 5.1.26100.8737 | Path inventory and bounded content searches |
| Private pre-copy audit | Git for Windows | 2.51.0.windows.1 | Tracked, untracked, and 39-commit history review |
| Private and public audits | ripgrep | 15.1.0 | Credential, privacy, path, and configuration searches |
| Private pre-copy audit | Python | 3.12.4 | Structured inventory and metadata inspection |
| Private pre-copy audit | PyPDF2 | 3.0.1 | In-memory PDF text inspection |
| Public audit | detect-secrets | 1.5.0 | Baseline-based secret scanning |
| Public audit | Bandit | 1.9.4 | Python static security analysis |
| Public audit | Ruff | 0.15.21 | Python lint and import/static checks |
| Public dependency audit | pip-audit | 2.10.1 | Installed-distribution vulnerability audit |

Tool results are evidence from this release-preparation environment. A human
reviewer must repeat them on the exact commit and exact dependency set selected
for publication.

## Private Pre-Copy Audit

### Automated Inventory And Searches

The pre-copy review used commands equivalent to the following from the private
repository. Search expressions are abbreviated here to avoid publishing a
reusable list of any project-specific identifiers; provider-key, credential,
private-key, JWT, URL-credential, personal-data, storage, recording, and
machine-path families were all covered.

```powershell
git status --short --untracked-files=all
git ls-files
git rev-list --all --count
rg --hidden --glob '!.git/**' '<credential-and-privacy-signatures>' .
git log -p --all --full-history | rg '<credential-and-privacy-signatures>'
Get-ChildItem -Recurse -Force -File | Select-Object FullName, Length
```

Additional read-only checks inventoried environment-variable access, provider
clients, authentication/session code, query parameters, private URLs and IPs,
absolute paths, Flask debug/bind settings, SQLite and Chroma persistence,
logs, job files, caches, uploads, audio/video files, and model assets.

### Manual Inspection

Manual review covered the Flask entry points, authentication and SSE routes,
provider construction, AMS/CRM/RAG/LCM storage code, MCM and EAS modules,
engineering packs, SIS prompts and drafts, CSC capture/transcription/TTS code,
templates, browser JavaScript, tests, raster images, and locally available PDF
text. Raster inspection was necessary because text scanners cannot detect
credentials displayed inside screenshots.

### Private Findings

| Finding | Disposition | Remaining action |
| --- | --- | --- |
| Three screenshots display two genuine session bearer tokens. | All three images were excluded. Committed lifecycle evidence shows random, process-local, in-memory sessions with 24-hour expiration. The screenshots entered the legacy repositories on June 25, 2026, so under that implementation the sessions expired by June 26, 2026 at the latest; any restart also invalidated them. No role password or evidence of misuse was found. | Present validity is reasonably excluded without claiming misuse was impossible. Replace or remove the legacy screenshots as repository hygiene; never reproduce a token or affected URL. |
| One screenshot displays private operational logs, provider activity, timestamps, and memory/runtime details. | Excluded. | Treat the image and any prior copies as private operational data. |
| Two named home-page screenshots contain memory-backed output and personal context; other UI captures were not provenance-cleared. | All private UI screenshots were excluded. | Use only newly generated synthetic/mock screenshots after human visual review. |
| `job_store/**` contains 212 JSON records and temporary artifacts totaling about 31 MB. Records include prompts, outputs, owner identifiers, reports, and a possible phone-number pattern. | Entire store excluded. Individual record names are not published because they may themselves identify private activity. | Retain and dispose of the private data under the private system's policy; do not use it as public test data. |
| `email_addresses.txt` contains 167 addresses. | Excluded. | Do not migrate, quote, or derive public fixtures from it. |
| The private `.gitignore` is UTF-16 LE and is not honored by Git. | Not copied. A new UTF-8 `.gitignore` was created and reviewed. | Verify ignore behavior on the exact release commit. |

No high-confidence literal provider key, private-key header, JWT,
URL-embedded text credential, or secret assignment was found across the
private working tree and its 39 commits. The separate screenshot finding was
resolved for this release through the documented expiration and in-memory
lifecycle analysis above. That conclusion does not prove misuse was impossible
and does not remove the legacy screenshots from their repositories.

## Public Repository Audit

### Secret Detection

The public tree was scanned with a checked-in detect-secrets baseline:

```powershell
detect-secrets scan --all-files --exclude-files '<Git/cache/license exclusions>' > .secrets.baseline
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
```

The final baseline contains 30 candidates across 11 files. Every entry was
manually reviewed: 20 are duplicated generated SHA-256 evidence hashes, and
the remaining ten are configuration-key names, defensive redaction examples,
or unmistakably synthetic test sentinels. No known active credential,
production token, private key, private user data, provider account identifier,
or voice identifier was accepted into the baseline.

Manual credential-signature and machine-path searches were also run with
`rg`. They found no credential value, private absolute path, private host,
production domain requirement, private email list, job record, memory record,
recording, or persistence database in the public release tree.

After all 11 release commits were created, `detect-secrets-hook` was rerun
against every tracked file and manual credential-signature and machine-path
searches were rerun across `git log -p --all --full-history`. All three checks
completed without an unbaselined finding. Secret-scan status is **locally
clean; human publication confirmation remains pending**. These checks must be
repeated if any commit changes and immediately before the first remote push.

### Static Security Analysis

The normal source scan and the separately bounded MCM scan use:

```powershell
bandit -c pyproject.toml -r src
bandit -r src/sos/computation/mcm.py -s B105,B112,B608
ruff check --no-cache .
ruff format --check --no-cache .
```

Both Bandit scans completed cleanly. The large inherited MCM module is scanned
separately so only three manually reviewed false-positive rule classes are
disabled for that file:

- `B105`: domain vocabulary and schema aliases were misidentified as hardcoded
  passwords;
- `B112`: deliberate best-effort parsing branches continue after rejecting an
  unusable candidate;
- `B608`: human-readable SQL examples and diagnostic strings are not executed
  as SQL.

All other Bandit rules remain active for MCM. Ruff 0.15.21 lint and formatting
checks were clean at the recorded audit point. The MCM evaluator also received
explicit size, depth, finite-number, exponent, collection, and result bounds
to prevent resource-exhaustion expressions from reaching deterministic
computation.

### Dependency Vulnerability Audit

An initial audit of the optional persistence environment identified a critical
pre-authentication code-injection advisory in the ChromaDB 1.x dependency
line. No fixed release was reported at the audit date. ChromaDB was therefore
removed from declared installation extras for 0.1.0; the adapter remains
source-visible but cannot be enabled through the public package metadata.

The final reduced environment contained 63 installed distributions and was
audited with:

```powershell
python -m pip_audit --strict --disable-pip --no-deps -r <exact-third-party-freeze>
```

`pip-audit` reported no known vulnerabilities in that 63-distribution
environment. This is not a claim about every resolver result permitted by the
project's version ranges, operator-supplied Ollama/model software, cloud
services, or future installations. Re-run the audit against the exact locked
artifacts selected for release.

### 2026-07-25 Working-Tree Reverification

The reconciled public working tree was reverified before final report updates:

- 172 of 172 offline tests passed with 32% branch-aware source coverage; the
  large MCM module had 16% line coverage and remains a material semantic and
  engineering-validation risk;
- Ruff lint and format checks passed, both bounded Bandit scans reported zero
  issues, the reproducible evidence check passed, and JavaScript syntax passed;
- sdist and wheel builds succeeded, and an installed-wheel smoke test verified
  health, AGPL metadata/license availability, evidence, and all 18 engineering
  pack files;
- project-scoped `pip-audit` found no known vulnerabilities in the declared
  dependency set;
- a baseline-aware all-files secret scan found no unbaselined findings, and
  bounded public-history searches found no high-confidence credential, private
  path, or media/database/key artifact candidates.

The release code was also hardened to avoid returning configured model
identifiers in session, chat, stream, and lifecycle metadata; to remove the
session-derived TTS response header; and to expose an explicit secure-cookie
configuration switch for HTTPS deployment.

Two qualifications remain. The general machine Python environment has
unrelated dependency conflicts and includes a non-PyPI language model that
prevents a strict machine-wide audit. Before creation of the release-candidate
commit, staged-candidate verification was completed for 40 changed paths in a
193-file indexed tree: its complete cached diff was inspected, the
baseline-aware `detect-secrets-hook` passed without mutating
`.secrets.baseline`, and all other staged technical checks passed. Exact-commit
and release-artifact verification was required after commit creation, with the
results recorded without modifying the exact commit being verified. At the
time this record was prepared, B-01 through B-08 and all applicable human
publication gates remained open.

### 2026-07-27 Private-Reference Reconciliation

Private commit `df0230b9386437a12d8ac4b2c65bf37d68eee9a2` was confirmed as a
descendant of the previously reviewed `ceca0f5` reference. Its committed delta
contains the revised private PGM, a small host activation call-site adjustment,
and a private EAS example PDF. None of those files or their operative contents
was copied into the public repository.

The PGM delta revises prompt-level governance and adds an emergency-claim and
tool-action boundary. Public documentation records only that emergency
assertions are not thereby verified and consequential tool actions require
authorization and applicable host controls. Prompt text is not deterministic
enforcement.

The new private PDF remains excluded. A bounded in-memory inspection found no
credential signature, embedded URL credential, email-like value, or absolute
local path in extracted text, but that automated result is not provenance,
privacy, or publication clearance.

After this documentation-only reconciliation, 41 targeted governance/web tests
and the complete 172-test offline suite passed. Markdown-link, baseline-aware
secret, absolute-path, sensitive-artifact, and diff-whitespace checks also
passed. No runtime or test file changed during the reconciliation.

## Security And Privacy Remediations

- Replaced the production monolith with a package factory, session ownership,
  CSRF checks, bounded in-memory jobs, and authorization checks on SSE/job
  access.
- Removed query-string and browser-local-storage authentication patterns from
  the public interface.
- Made the deterministic mock provider the no-credential default; cloud SDKs
  are lazy and optional.
- Bound development services and Ollama to loopback by default and rejected
  debug mode on non-loopback binds.
- Replaced persistent private conversation/memory stores with empty,
  session-scoped interfaces; raw-content logging and retention are disabled by
  default.
- Scoped DIM deduplication by session and namespace to avoid cross-session
  existence disclosure.
- Required explicit browser action for microphone and camera capture, exposed
  global capture/playback state, rejected persistent sensory retention, and
  used raw in-memory WAV requests instead of multipart temporary spooling.
- Kept provider keys, TTS voice IDs, model selection, and service locations in
  environment variables with empty/example-only values.
- Excluded all private stores, screenshots, recordings, caches, databases,
  logs, deployment state, model weights, and unclear third-party assets.
- Added restrictive public ignores for secrets, databases, Chroma persistence,
  logs, uploads, recordings, local models, coverage, and test artifacts.

## Remaining Risks And Required Actions

1. Replace or remove the credential-bearing legacy screenshots and consider
   their repository histories as a separate hygiene task. Do not reproduce a
   token or affected URL.
2. Repeat detect-secrets, manual `rg` signatures, Bandit, Ruff, tests, evidence
   reproduction, and dependency auditing immediately before the first push.
3. Repeat the complete new Git-history scan if any commit is added or amended.
   A later deletion cannot make a committed secret safe.
4. Review every release screenshot visually; OCR/text scanners are
   insufficient.
5. Preserve the July 28, 2026 release-owner IP, privacy,
   dependency-license, engineering-pack, and provider-boundary decisions
   documented in `PUBLIC_PUSH_CHECKLIST.md`.
6. Use the tested, monitored private vulnerability-reporting address in
   `SECURITY.md`; enable GitHub Private Vulnerability Reporting only if it is
   separately configured and tested.
7. Treat optional provider calls as external data disclosure. Operators remain
   responsible for provider terms, data retention, regional requirements, and
   model licenses.

## Release Confirmation

No known active credential, private memory, user conversation, production
authentication data, private voice identifier, or private operational record
was copied into the public repository. This confirmation is limited to the
audited local tree. The excluded screenshot sessions are reasonably determined
inactive by their 24-hour, process-local, in-memory lifecycle and June 25, 2026
repository-entry date; no claim is made that misuse was impossible. This audit
does not authorize a push or visibility change.
