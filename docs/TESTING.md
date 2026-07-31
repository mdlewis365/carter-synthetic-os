<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Testing

The standard test suite is designed to run without network access, cloud credentials, paid APIs, Ollama, a microphone, or a camera. Provider calls in standard tests use deterministic fakes or mocks.

## Setup And Commands

Install the development extra from the repository root:

```console
python -m pip install -e ".[dev]"
```

Run the complete non-network suite, including tests marked `slow`:

```console
python -m pytest -m "not local_model and not cloud_provider"
```

PowerShell and POSIX convenience wrappers are available as `scripts/run_tests.ps1` and `scripts/run_tests.sh`. They run the faster release-check selection, omitting `local_model`, `cloud_provider`, and `slow` while collecting terminal coverage. Use the explicit `python -m pytest` command above when verifying the complete non-network selection.

## Markers

| Marker | Purpose | Standard suite expectation |
| --- | --- | --- |
| `unit` | Isolated deterministic behavior | Included. |
| `integration` | Cross-module or Flask workflow | Included when non-network. |
| `smoke` | Startup and representative public workflow | Included when non-network. |
| `local_model` | Requires an operator-run local model | Opt-in. |
| `cloud_provider` | Requires a real cloud service | Opt-in only; may incur cost. |
| `sensory` | CSC behavior, normally with synthetic media/transcripts | Non-device tests included; real devices opt-in. |
| `slow` | Longer-running checks | May be excluded during quick iteration. |

Run a subset with pytest marker expressions, for example:

```console
python -m pytest -m "unit or integration"
python -m pytest -m "not local_model and not cloud_provider and not slow"
```

Do not run real provider integration tests merely to validate a pull request. They require deliberate opt-in, approved credentials/test data, and cost controls.

## Clean Windows Installed-Wheel Smoke

The `Windows installed-wheel smoke` GitHub Actions job builds the wheel on
`windows-latest`, installs it non-editably into a new virtual environment
without system site-packages, clears inherited `PYTHONPATH`, and sets
`PYTHONTZPATH` to an empty value. The reusable
`scripts/verify_installed_wheel.py` harness then confirms that:

- Carter and its public packages import from the isolated environment's
  `site-packages`, not the checkout;
- neither `tzdata` nor an available `ZoneInfo("UTC")` lookup masks the default
  UTC path;
- package version and `AGPL-3.0-only` metadata are present; and
- health, session/CSRF, Carter chat, EAS, SIS, CSC, packaged evidence,
  templates/static files, license text, and all 18 engineering-pack files are
  reached and pass.

The harness compares its completed steps with a fixed manifest, so a failure
after Carter chat cannot be reported as a partial success. Release verification
also runs the same harness against the wheel with all declared runtime extras
installed.

## Coverage Areas

Public tests cover configuration and secret-free startup, request normalization, schema validation, memory contracts, governance, MCM, EAS pack selection and decision records, SIS mode/workflow behavior, CSC session isolation and text classification, authorization, SSE ownership/behavior, provider failures, and mock end-to-end execution.

The final release report is the authoritative record of tests collected, passed, failed, skipped, and measured coverage for the prepared commit. Documentation does not claim a passing count until those commands have actually run.

## Reproducible Evidence

The evidence case under `examples/evidence/` uses synthetic engineering inputs and the deterministic mock backend. Regenerate it from the repository root with:

```console
python -m examples.evidence.run_case
```

The manifest records software/Python versions, timestamp, backend, deterministic status, hashes, and test status. Checked-in artifacts should change only through this generator.

## Test Data Rules

- Use unmistakably synthetic identities, requests, engineering values, transcripts, and session IDs.
- Never use private Carter memories, production logs, real credentials, account identifiers, recordings, or confidential inventions.
- Mock cloud SDKs at the provider boundary.
- Keep random/time inputs fixed when asserting deterministic artifacts.
- Verify failures and review-required states, not only successful paths.

## Limits Of Testing

Passing tests do not establish professional engineering validity, scientific validation, model quality, patentability, regulatory compliance, production security, or compatibility with every Ollama model/provider version. Hardware media behavior and real cloud integrations vary by browser, device, account, region, and upstream service.
