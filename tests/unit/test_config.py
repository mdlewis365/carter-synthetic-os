# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

from __future__ import annotations

import pytest

from shared.config import ConfigError, load_settings

pytestmark = pytest.mark.unit


def test_secret_free_startup_uses_ephemeral_signing_key() -> None:
    settings = load_settings({})

    assert settings.provider == "mock"
    assert settings.host == "127.0.0.1"
    assert settings.debug is False
    assert settings.enable_memory is False
    assert settings.enable_sensory_retention is False
    assert settings.ephemeral_secret is True
    assert len(settings.flask_secret_key) >= 32


def test_placeholder_secret_is_never_used_for_signing() -> None:
    settings = load_settings({"FLASK_SECRET_KEY": "replace-with-a-long-random-secret"})

    assert settings.ephemeral_secret is True
    assert settings.flask_secret_key != "replace-with-a-long-random-secret"


def test_public_configuration_never_contains_secret_value() -> None:
    configured = "synthetic-test-secret-that-is-long-enough-12345"
    settings = load_settings({"FLASK_SECRET_KEY": configured})

    public = settings.public_dict()

    assert settings.ephemeral_secret is False
    assert "flask_secret_key" not in public
    assert configured not in repr(public)


def test_public_configuration_omits_paths_urls_and_model_identifiers() -> None:
    settings = load_settings(
        {
            "CARTER_DATA_DIR": "C:/private/synthetic-data",
            "OLLAMA_MODEL": "private-model-id",
        }
    )

    public = settings.public_dict()

    assert "private" not in repr(public)
    assert "127.0.0.1:11434" not in repr(public)
    assert public["ollama_endpoint_scope"] == "loopback"


def test_remote_ollama_is_rejected_by_default() -> None:
    with pytest.raises(ConfigError, match="Remote Ollama"):
        load_settings({"OLLAMA_BASE_URL": "https://models.example.invalid"})


def test_unimplemented_sensory_retention_fails_closed() -> None:
    with pytest.raises(ConfigError, match="not implemented"):
        load_settings({"CARTER_ENABLE_SENSORY_RETENTION": "true"})


def test_remote_ollama_requires_explicit_opt_in() -> None:
    settings = load_settings(
        {
            "OLLAMA_BASE_URL": "https://models.example.invalid",
            "CARTER_ALLOW_REMOTE_OLLAMA": "true",
        }
    )

    assert settings.allow_remote_ollama is True


def test_ollama_url_rejects_embedded_credentials() -> None:
    with pytest.raises(ConfigError, match="credentials"):
        load_settings(
            {
                "OLLAMA_BASE_URL": "http://user:password@127.0.0.1:11434",
            }
        )


def test_non_loopback_bind_requires_explicit_opt_in() -> None:
    with pytest.raises(ConfigError, match="Non-loopback"):
        load_settings({"CARTER_HOST": "0.0.0.0"})


def test_debug_mode_is_rejected_on_public_bind() -> None:
    with pytest.raises(ConfigError, match="DEBUG"):
        load_settings(
            {
                "CARTER_HOST": "0.0.0.0",
                "CARTER_ALLOW_PUBLIC_BIND": "true",
                "CARTER_DEBUG": "true",
            }
        )


def test_invalid_boolean_is_not_silently_enabled() -> None:
    with pytest.raises(ConfigError, match="CARTER_DEBUG"):
        load_settings({"CARTER_DEBUG": "perhaps"})
