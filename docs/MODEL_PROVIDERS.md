<!-- SPDX-License-Identifier: AGPL-3.0-only -->

# Model Providers

Model integrations are replaceable boundaries. The core release uses a deterministic mock provider and does not require credentials, network access, a paid API, or a downloaded model.

## Provider Summary

| Provider | Installation | Data boundary | Default behavior |
| --- | --- | --- | --- |
| Mock | Core package | Local deterministic fixtures | Default; clearly labeled as not a language model. |
| Ollama | Optional `ollama` extra and separately installed Ollama service/model | Local service on `127.0.0.1` by default | Controlled unavailable-provider error if service/model is missing. |
| OpenAI | Optional `openai` extra | Request data is sent to OpenAI | Disabled until package, key, and model are configured. |
| Anthropic | Optional `anthropic` extra | Request data is sent to Anthropic | Disabled until package, key, and model are configured. |
| Google (`gemini` selector alias) | Optional `google` extra | Request data, and CSC audio when selected, is sent to Google | Disabled until package, key, model, and relevant CSC setting are configured. |
| ElevenLabs | CSC uses the Python standard-library HTTPS client; no SDK extra | Response text is sent to ElevenLabs | Disabled until key and voice ID are configured. |

Provider names and model identifiers are configuration, not repository secrets. API keys, account identifiers, and voice identifiers must never be committed.

Install only the boundary needed by the deployment, for example:

```console
python -m pip install -e ".[ollama]"
python -m pip install -e ".[openai]"
python -m pip install -e ".[anthropic]"
python -m pip install -e ".[google]"
python -m pip install -e ".[csc]"
```

`.[all]` installs all runtime extras but is unnecessary for the mock demonstration. Development/test tools use `.[dev]`.

No ChromaDB extra is published in `0.1.0`. The adapter boundary is included for
source review, but current ChromaDB 1.x packages are blocked by
`PYSEC-2026-311` / `CVE-2026-45829` until an audited fixed release exists.

## Mock Mode

```dotenv
CARTER_PROVIDER=mock
CARTER_DEFAULT_MODEL=mock-v1
```

Mock mode emits deterministic synthetic fixtures designed to exercise normalization, planning, validation, deterministic computation, governance, streaming, and reporting. It must not be described as a language model or as evidence of model quality. It is the mode used by the basic demonstration and non-network tests.

## Local Ollama Mode

Install Ollama separately, obtain a model under terms acceptable to you, and configure its model identifier. The project does not distribute weights or grant rights to any model.

```dotenv
CARTER_PROVIDER=ollama
CARTER_DEFAULT_MODEL=your-installed-model
OLLAMA_BASE_URL=http://127.0.0.1:11434
CARTER_ALLOW_REMOTE_OLLAMA=false
```

Typical operator steps are:

```console
ollama pull <model>
ollama serve
```

Install the repository's Ollama optional extra before selecting the provider. Version `0.1.0` has no model-specific certification or allowlist: an operator may configure an installed text-generation model compatible with Ollama's `/api/generate` response contract. Specific model quality, context size, tool use, and structured-output reliability are not guaranteed.

Memory requirements are model-specific. Consult the selected model's official documentation and account for quantization, context length, concurrent requests, and GPU/CPU placement. No blanket RAM or VRAM requirement is claimed here.

The loopback restriction is deliberate. Remote Ollama endpoints expand the disclosure and server-side request-forgery boundary and require the explicit `CARTER_ALLOW_REMOTE_OLLAMA` opt-in plus independent network controls.

## Cloud Providers

Cloud integrations are optional and use operator-supplied environment variables:

```dotenv
CARTER_PROVIDER=openai
CARTER_DEFAULT_MODEL=provider-model-id
OPENAI_API_KEY=
```

Use `CARTER_PROVIDER=anthropic` with `ANTHROPIC_API_KEY`, or `CARTER_PROVIDER=google` with `GOOGLE_API_KEY`, for the other cloud adapters. In every case `CARTER_DEFAULT_MODEL` selects the provider model. Do not use a model identifier from one provider with another provider.

Selecting a cloud provider sends the governed request and necessary context outside the local process. Provider-side retention, training, abuse monitoring, residency, subprocessors, billing, and deletion are controlled by the operator's agreement and provider settings, not this repository. Do not send confidential, regulated, export-controlled, personal, or third-party data unless you have authority and an appropriate provider configuration.

Provider construction performs no service call and SDK imports are lazy. If an extra is absent, credentials are missing, a model is unspecified, or a service is unreachable, generation raises a sanitized `ProviderError` such as `missing_dependency`, `missing_api_key`, `model_not_configured`, `generation_failed`, or Ollama `unavailable`. Standard installation and tests do not fall back silently from local/mock mode to a paid provider.

## CSC Providers

CSC transcription is disabled by default:

```dotenv
CSC_TRANSCRIPTION_PROVIDER=disabled
CSC_INTERPRETATION_BACKEND=mock
```

Selecting Google transcription sends captured audio to Google. Selecting Ollama interpretation sends transcript context to the configured Ollama endpoint. Selecting ElevenLabs TTS sends response text to ElevenLabs and requires both `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`. See [CSC.md](CSC.md) before enabling media features.

## Failure And Cost Controls

- Cloud credentials are never required for import, startup, tests, or the mock demo.
- A provider is not called merely because its key exists; it must be selected.
- Provider failures remain explicit and do not generate fake success output.
- Tests use fakes/mocks unless explicitly marked as opt-in provider integration tests.
- Operators are responsible for rate limits, quotas, billing alerts, data-processing terms, and key rotation.
