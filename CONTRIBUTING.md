<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Contributing

Thank you for considering a contribution to Carter Synthetic OS. The project accepts focused improvements that preserve its governed, auditable, privacy-conscious boundaries.

## License Of Contributions

Unless a separate written agreement signed by the copyright owner says otherwise, every contribution accepted into this repository is distributed under **GNU Affero General Public License v3.0 only** (`AGPL-3.0-only`). No contributor license agreement is required by this repository.

By submitting a contribution, you represent that you have the right to submit it under `AGPL-3.0-only`. Keep your own copyright notice when appropriate. Do not submit employer-owned, client-owned, confidential, export-controlled, patent-sensitive, or third-party material unless you have documented authority.

## Before Opening A Change

- Search existing issues and pull requests.
- Use a private security report for vulnerabilities; see [SECURITY.md](SECURITY.md).
- Keep implementation, tests, documentation, and claims aligned.
- Do not include credentials, personal data, conversations, memories, logs, recordings, account identifiers, production endpoints, proprietary prompts, model weights, datasets, or uncleared assets.
- Identify third-party code/data/assets and include their source, version, license, and required notices.
- Disclose material use of generated code or text in the pull request and confirm that you reviewed it and have the right to contribute it.

## Development Setup

Use a supported Python version in an isolated environment:

```console
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Activate the environment using the command appropriate for your shell. `.env.example` is a placeholder reference; the application reads the process environment and does not require a dotenv loader. If your local tooling uses a `.env`, keep the populated file untracked.

## Checks

Run the standard non-network suite before submitting:

```console
python -m pytest -m "not local_model and not cloud_provider"
python -m ruff check .
python -m ruff format --check .
python -m build
```

The repository wrappers under `scripts/` run the faster non-network selection with coverage and also omit `slow` tests. Do not use real cloud credentials or incur provider charges in a standard test. Mark opt-in integration tests with the appropriate `local_model`, `cloud_provider`, `sensory`, or `slow` marker.

Add tests proportional to the behavior changed. Security and cross-session changes need negative tests. Deterministic evidence output must be regenerated with `python -m examples.evidence.run_case`, never edited to look runtime-generated.

## Pull Requests

A pull request should:

- explain the problem, implementation, and user-visible effect;
- identify security, privacy, provider, persistence, and license impact;
- list commands actually run and their exact results;
- distinguish implemented, tested, experimentally validated, and unvalidated claims;
- update relevant architecture, threat-model, configuration, and limitation documents;
- avoid unrelated formatting or refactoring churn.

Maintainers may ask for provenance evidence, a smaller change, additional tests, or independent professional review. Acceptance does not certify the contribution for engineering, scientific, patent, safety, legal, or production use.

## Engineering And Ideation Contributions

EAS changes must preserve the professional-review warning and deterministic/probabilistic boundary. Engineering packs require traceable first-party authorship or redistribution permission and must not reproduce protected standards.

SIS changes must preserve hypothesis/candidate labeling. Do not submit confidential inventions or claim novelty, patentability, prior-art clearance, safety, or experimental validation without defensible independent evidence.

CSC changes must keep microphone and camera disabled until explicit activation, display active state, isolate sessions, and retain nothing by default. A cloud transfer requires clear documentation and tests.

## Conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
