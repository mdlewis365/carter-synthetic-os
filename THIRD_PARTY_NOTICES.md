<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Third-Party Notices

Carter Synthetic OS is licensed under `AGPL-3.0-only`, but it depends on separately distributed third-party packages and can connect to third-party services and models. Those materials retain their own copyright, license, service, model, and data terms.

This file is a notice and review aid, not legal advice, a complete transitive-dependency bill of materials, or a conclusion that every possible optional installation is license-compatible. Versions and licenses must be rechecked against the built release and upstream license texts before publication and for every update.

On July 28, 2026, Michael D. Lewis accepted the documented technical
dependency-license evidence for this Initial Public Research Release. This
release-owner acceptance is not a legal opinion. No dependency source is
bundled or vendored in the project wheel, and future dependency resolutions or
rebuilt artifacts require a fresh license, notice, vulnerability, and
package-content audit.

## Declared Runtime Dependencies

| Dependency | Declared range | Reported upstream license | Use | Review status |
| --- | --- | --- | --- | --- |
| Flask | `>=3.0,<4` | BSD-3-Clause/BSD metadata | Core web application | Verify exact installed version and bundled license text. |
| OpenAI Python library | `>=1.66,<3` | Apache-2.0 metadata | Optional OpenAI provider | Verify installed distribution and notices. |
| Anthropic Python library | `>=0.40,<1` | MIT metadata | Optional Anthropic provider | Verify installed distribution and notices. |
| Google Gen AI Python SDK | `>=1.0,<2` | Apache-2.0 metadata | Optional Google generation/transcription | Verify installed distribution and notices. |

The Ollama adapter currently declares no Python package dependency; it communicates with an operator-run service. Ollama software, downloaded model weights, tokenizers, templates, and training data are separately obtained and must be reviewed under their own terms.

The first-party Chroma adapter source remains available for review, but release
`0.1.0` does not declare or install ChromaDB. The current 1.x package line is
affected by critical pre-authentication code injection advisory
`PYSEC-2026-311` / `CVE-2026-45829`, and no fixed release was reported during
the July 13, 2026 audit. Re-enabling this dependency requires a fixed version,
fresh vulnerability and license audits, adapter tests, and human approval.

## Build, Test, And Audit Tools

These development/build dependencies are not imported by the normal application, but their distributions and generated artifacts remain subject to their own terms.

| Dependency | Declared range | Reported upstream license | Purpose |
| --- | --- | --- | --- |
| setuptools | `>=77.0.3` | MIT metadata | Build backend. |
| wheel | Unbounded build requirement | MIT metadata | Wheel construction. |
| Bandit | `>=1.7,<2` | Apache-2.0 metadata | Static security checks. |
| build | `>=1.2,<2` | MIT metadata | Package build verification. |
| detect-secrets | `>=1.5,<2` | Apache-2.0 metadata | Secret-detection checks. |
| pip-audit | `>=2.7,<3` | Apache-2.0 metadata | Dependency vulnerability audit. |
| pip-licenses | `>=5,<6` | MIT metadata | Installed-license inventory. |
| pytest | `>=8.2,<9` | MIT metadata | Test runner. |
| pytest-cov | `>=5,<7` | MIT metadata | Coverage integration. |
| Ruff | `>=0.8,<1` | MIT metadata | Lint and format checks. |

Reported licenses above come from upstream package/project metadata observed during release preparation. Metadata can be incomplete or inconsistent; the exact installed artifacts and upstream license files are the controlling evidence.

## Transitive Dependencies

Flask, cloud SDKs, and development tools install transitive dependencies that are not enumerated here. The point-in-time `LICENSE_COMPATIBILITY_REPORT.md` records the audited environment and unresolved questions. A release reviewer should generate a locked dependency inventory, run `pip-licenses`, inspect ambiguous `License-File` metadata, and preserve any required notices in distributed artifacts.

No dependency should be described as AGPL-compatible merely because it is open source. Compatibility and distribution obligations require human review of the actual version, use, linkage/distribution method, and full license text.

## Services, Models, And Data

OpenAI, Anthropic, Google, ElevenLabs, Ollama, and any model publisher impose terms independent of package licenses. API terms govern hosted processing; model licenses may restrict use or redistribution; training-data and output rights may raise separate questions. This repository does not distribute provider accounts, API credentials, model weights, cloned voices, fonts, datasets, or provider-owned media.

CSC accesses the optional ElevenLabs text-to-speech service through a bounded
HTTPS request and does not depend on or redistribute the ElevenLabs Python SDK.

Operators must review model cards/licenses and provider data terms before use. Installing an optional extra is not permission to send data to a service and is not a license grant for any model.

## Assets And Documentation

No private screenshots, audio, cloned voice, production recording, third-party font, model, or raster asset from the audited private repository is included. Mermaid source in the Markdown documentation is first-party text; rendering services supplied by a documentation host are not bundled with this repository.

Engineering packs are treated as first-party release material. Michael D.
Lewis recorded the release-owner provenance/IP decision for all 18 included
pack files on July 28, 2026. They must not be assumed to reproduce or replace
any protected engineering standard, and that owner decision is not a legal
opinion or independent professional validation.

## Full License Texts

Third-party license texts are available from each installed distribution's metadata and upstream source repository. The project AGPL text in [LICENSE](LICENSE) applies only to first-party Carter Synthetic OS material except where a file explicitly says otherwise.
