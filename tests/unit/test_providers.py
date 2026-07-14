# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import json
from io import BytesIO

import pytest

from sos.models import (
    ModelProvider,
    ModelRequest,
    ProviderError,
    available_providers,
    create_provider,
)

pytestmark = pytest.mark.unit


def test_model_request_supports_structured_context_and_system_alias() -> None:
    request = ModelRequest(
        "classify",
        system="synthetic-system",
        context={"value": 3},
    )

    assert request.system_prompt == "synthetic-system"
    assert request.system == "synthetic-system"
    assert "structured_context" in request.rendered_prompt
    assert '"value":3' in request.rendered_prompt


def test_model_request_rejects_unstructured_context_and_boolean_token_count() -> None:
    with pytest.raises(TypeError, match="context must be a mapping"):
        ModelRequest("synthetic", context=["not", "a", "mapping"])
    with pytest.raises(TypeError, match="max_tokens must be an integer"):
        ModelRequest("synthetic", max_tokens=True)


def test_mock_provider_is_deterministic_labeled_and_not_a_language_model() -> None:
    provider = create_provider("mock")
    request = ModelRequest("synthetic public request")

    first = provider.generate(request)
    second = provider.generate(request)

    assert isinstance(provider, ModelProvider)
    assert first == second
    assert first.content == first.text
    assert first.text.startswith("[Mock provider: deterministic synthetic output]")
    assert first.metadata["deterministic"] is True
    assert first.metadata["language_model_invoked"] is False


def test_mock_provider_stream_reassembles_exact_response() -> None:
    provider = create_provider("mock", settings={"chunk_size": 7})
    request = ModelRequest("stream this synthetic fixture")

    assert "".join(provider.stream(request)) == provider.generate(request).text


def test_mock_csc_fixture_returns_deterministic_json() -> None:
    provider = create_provider("mock")
    response = provider.generate(
        ModelRequest("classify", metadata={"mock_fixture": "csc_attention_v1"})
    )

    assert json.loads(response.text)["reason"] == "deterministic synthetic CSC fixture"


def test_provider_registry_has_all_public_boundaries() -> None:
    assert set(available_providers()) == {
        "anthropic",
        "gemini",
        "google",
        "mock",
        "ollama",
        "openai",
    }
    with pytest.raises(ProviderError) as error:
        create_provider("unsupported")
    assert error.value.code == "unknown_provider"


@pytest.mark.parametrize(
    ("name", "environment_key"),
    [
        ("openai", "OPENAI_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("google", "GOOGLE_API_KEY"),
    ],
)
def test_cloud_providers_fail_before_import_or_network_without_key(
    monkeypatch: pytest.MonkeyPatch, name: str, environment_key: str
) -> None:
    monkeypatch.delenv(environment_key, raising=False)
    provider = create_provider(name, model="synthetic-model")

    with pytest.raises(ProviderError) as error:
        provider.generate(ModelRequest("synthetic"))

    assert error.value.code == "missing_api_key"


def test_openai_responses_sdk_boundary_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs["model"] == "synthetic-model"
            assert kwargs["input"] == "synthetic request"
            return type(
                "FakeResponse",
                (),
                {
                    "output_text": "synthetic provider output",
                    "usage": type(
                        "FakeUsage",
                        (),
                        {"input_tokens": 2, "output_tokens": 3},
                    )(),
                },
            )()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            assert kwargs == {"api_key": "synthetic-key"}
            self.responses = FakeResponses()

    provider = create_provider(
        "openai",
        model="synthetic-model",
        settings={"api_key": "synthetic-key"},
    )
    fake_module = type("FakeOpenAIModule", (), {"OpenAI": FakeOpenAI})
    monkeypatch.setattr(
        "sos.models.openai.importlib.import_module",
        lambda name: fake_module if name == "openai" else None,
    )

    response = provider.generate(ModelRequest("synthetic request"))

    assert response.text == "synthetic provider output"
    assert response.usage == {"input_tokens": 2, "output_tokens": 3}


def test_google_sdk_boundary_applies_generation_limits_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    class FakeConfig:
        def __init__(self, **kwargs):
            seen["config"] = kwargs

    class FakeModels:
        def generate_content(self, **kwargs):
            seen["request"] = kwargs
            return type("FakeResponse", (), {"text": "synthetic google output"})()

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs == {"api_key": "synthetic-key"}
            self.models = FakeModels()

    fake_module = type("FakeGoogleModule", (), {"Client": FakeClient})
    fake_types = type(
        "FakeGoogleTypes",
        (),
        {"GenerateContentConfig": FakeConfig},
    )

    def fake_import(name: str):
        return {
            "google.genai": fake_module,
            "google.genai.types": fake_types,
        }[name]

    provider = create_provider(
        "google",
        model="synthetic-model",
        settings={"api_key": "synthetic-key"},
    )
    monkeypatch.setattr("sos.models.google.importlib.import_module", fake_import)
    request = ModelRequest(
        "synthetic request",
        system_prompt="synthetic system",
        max_tokens=321,
        temperature=0.25,
    )

    response = provider.generate(request)

    assert response.text == "synthetic google output"
    assert seen["config"] == {
        "system_instruction": "synthetic system",
        "max_output_tokens": 321,
        "temperature": 0.25,
    }
    assert seen["request"]["contents"] == "synthetic request"


def test_ollama_rejects_remote_endpoint_without_explicit_opt_in() -> None:
    with pytest.raises(ValueError, match="allow_remote"):
        create_provider(
            "ollama",
            model="synthetic-model",
            settings={"base_url": "https://models.example.invalid"},
        )


def test_ollama_string_false_does_not_enable_remote_access() -> None:
    with pytest.raises(ValueError, match="allow_remote"):
        create_provider(
            "ollama",
            model="synthetic-model",
            settings={
                "base_url": "https://models.example.invalid",
                "allow_remote": "false",
            },
        )


def test_ollama_missing_model_fails_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CARTER_DEFAULT_MODEL", raising=False)
    provider = create_provider("ollama", settings={"base_url": "http://127.0.0.1:11434"})

    with pytest.raises(ProviderError) as error:
        provider.generate(ModelRequest("synthetic"))

    assert error.value.code == "model_not_configured"


def test_ollama_generate_uses_lazy_urllib_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    seen: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data)
        seen["timeout"] = timeout
        return FakeResponse(
            json.dumps(
                {
                    "response": "synthetic local output",
                    "done_reason": "stop",
                    "prompt_eval_count": 4,
                    "eval_count": 3,
                }
            ).encode()
        )

    monkeypatch.setattr("sos.models.ollama.urlopen", fake_urlopen)
    provider = create_provider(
        "ollama",
        model="synthetic-local-model",
        settings={"base_url": "http://127.0.0.1:11434"},
    )
    response = provider.generate(ModelRequest("synthetic", context={"number": 2}))

    assert response.text == "synthetic local output"
    assert response.usage == {"prompt_eval_count": 4, "eval_count": 3}
    assert seen["url"] == "http://127.0.0.1:11434/api/generate"
    assert "structured_context" in seen["body"]["prompt"]
