<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# License Compatibility Report

Release: `0.1.0` (Initial Public Research Release)

Audit date: 2026-07-13

Audit environment: fresh Python 3.12.4 environment with all release extras,
except for the deliberately blocked ChromaDB dependency described below. Build,
test, and audit tool versions are recorded separately from that resolver result.

This is a technical inventory and release-engineering review, not legal advice.
Package metadata can be incomplete or inaccurate, and a reported license does
not by itself establish compatibility for every use or distribution. A qualified
human reviewer must examine the exact artifacts, full license texts, notices,
linkage and distribution method before publication.

## Method And Results

The fresh audit environment resolved 63 third-party distributions, including
direct and transitive dependencies. Installed distribution metadata and bundled
license files were inspected with `pip-licenses 5.5.5`; `pip check` reported no
broken requirements; and `pip-audit 2.10.1` reported no known vulnerabilities in
that safe environment.

The detected versions below are the versions examined for this release audit,
not additional pins beyond the ranges in `pyproject.toml`. A future resolver run
can select different versions and requires a new license and vulnerability audit.

Compatibility status meanings:

- **No conflict identified**: the detected permissive license did not present an
  identified conflict with the project's planned AGPL distribution in this
  technical review; human legal approval remains required.
- **Tool only**: used to build, test, or audit the release and not imported by the
  normal application or bundled into its wheel.
- **Blocked**: not installed or enabled for the release because of an unresolved
  security or licensing gate.
- **Service terms separate**: no Python SDK is declared; operator-obtained
  service, model, or data terms still apply.

## Direct Runtime Dependencies

| Direct dependency | Detected version | Detected license | License evidence | Compatibility status | Unresolved questions |
| --- | ---: | --- | --- | --- | --- |
| Flask | 3.1.3 | BSD-3-Clause | Installed distribution metadata and bundled license file; upstream package metadata | No conflict identified | Confirm required copyright/license notice treatment for the exact release artifact and review transitive Werkzeug, Jinja, Click, ItsDangerous, Blinker, and MarkupSafe artifacts. |
| openai | 2.45.0 | Apache-2.0 | Installed distribution metadata and bundled license file; upstream package metadata | No conflict identified; optional extra | Preserve any required Apache notices and separately review OpenAI service/data terms. No credential or provider asset is distributed. |
| anthropic | 0.116.0 | MIT | Installed distribution metadata and bundled license file; upstream package metadata | No conflict identified; optional extra | Preserve the MIT notice and separately review Anthropic service/data terms. No credential or provider asset is distributed. |
| google-genai | 1.75.0 | Apache-2.0 | Installed distribution metadata and bundled license file; upstream package metadata | No conflict identified; optional `google`/`csc` extra | Preserve any required Apache notices and separately review Google service/data terms, including transcription use. No credential or provider asset is distributed. |

The core install declares only Flask. Cloud SDKs are optional and are not
required for mock mode, tests, or package installation.

## Service-Only Integrations

| Integration | Python SDK dependency | License/terms treatment | Status | Unresolved questions |
| --- | --- | --- | --- | --- |
| Ollama | None | The adapter uses the operator-run HTTP service. Ollama, downloaded models, tokenizers, templates, and weights retain their own licenses and terms. | Service terms separate | Review the exact Ollama release and every selected model before use; no weights are distributed here. |
| ElevenLabs | None | CSC uses a bounded HTTPS request to the operator-configured service. Provider service, voice, and data terms remain separate. | Service terms separate | Review service/data/voice rights before enabling TTS. No SDK, voice identifier, cloned voice, or audio asset is distributed here. |

## Direct Build, Test, And Audit Tools

| Direct dependency | Detected version | Detected license | License evidence | Compatibility status | Unresolved questions |
| --- | ---: | --- | --- | --- | --- |
| setuptools | 80.9.0 | MIT | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | Recheck the exact build backend artifact for each release. |
| wheel | 0.45.1 | MIT | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | Confirm generated wheels do not accidentally bundle tool code. |
| build | 1.2.1 | MIT | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | Recheck when the build environment changes. |
| pytest | 8.3.4 | MIT | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | None identified beyond routine version re-audit. |
| pytest-cov | 6.3.0 | MIT | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | Review its coverage dependency in the transitive inventory. |
| ruff | 0.15.21 | MIT | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | None identified beyond routine version re-audit. |
| bandit | 1.9.4 | Apache-2.0 | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | Preserve notices if the tool is ever redistributed rather than merely used. |
| detect-secrets | 1.5.0 | Apache-2.0 | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | Preserve notices if the tool is ever redistributed rather than merely used. |
| pip-audit | 2.10.1 | Apache-2.0 | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | Its advisory result is time-dependent and must be rerun immediately before publication. |
| pip-licenses | 5.5.5 | MIT | Installed distribution metadata and bundled license file; upstream package metadata | Tool only; no conflict identified | Metadata output is an inventory aid, not the controlling license text. |

## ChromaDB Block

The repository contains a first-party Chroma adapter source boundary for review,
but `chromadb` is not declared by the core, optional, `csc`, or `all` extras and
must not be installed or enabled for `0.1.0`.

An earlier isolated audit resolved `chromadb 1.5.9` and found critical advisory
`PYSEC-2026-311` / `CVE-2026-45829`, with no fixed release reported on
2026-07-13. That dependency was removed from the release extras. Chroma support
remains blocked until a fixed version exists and passes a fresh vulnerability
audit, dependency-license audit, adapter test run, and human security approval.
The safe 63-distribution audit result above does not include ChromaDB.

## Transitive Dependencies

The 63-distribution environment includes transitive packages from Flask and the
optional cloud SDKs. This report does not claim that their metadata alone proves
AGPL compatibility. Before public distribution, a human reviewer must retain and
review a complete machine-readable inventory for the final resolved environment,
inspect all ambiguous or compound license expressions and `License-File` entries,
and ensure that required attribution or notice files accompany any redistributed
artifact.

The application wheel must also be inspected to confirm that it contains only
first-party project files and intentionally packaged notices. Provider SDKs and
their transitive packages should remain separately installed dependencies, not
vendored source.

## Project And Asset Boundary

First-party Carter Synthetic OS material is offered under
`AGPL-3.0-only`. Third-party packages, services, models, model weights, datasets,
fonts, images, audio, and other assets do not become AGPL-licensed merely by being
used with the project. This release does not distribute provider SDK source,
model weights, cloned voices, private screenshots, recordings, or datasets.

The engineering packs are treated as first-party release material for technical
preparation, but their authorship, ownership, standards-derived content, patent,
and redistribution provenance require explicit human approval before publication.

## Compatibility Conclusion

No license conflict was identified in the examined direct package set, and the
safe environment was internally consistent and free of known vulnerabilities at
the time of the audit. This is not a final legal compatibility determination.
Publication remains blocked on the human IP, copyright, engineering-pack,
transitive-license, and final-artifact reviews listed in
`RELEASE_BLOCKERS.md` and `PUBLIC_PUSH_CHECKLIST.md`.
