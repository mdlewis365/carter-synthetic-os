# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs

"""Environment-only public configuration with conservative defaults."""

from __future__ import annotations

import ipaddress
import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


class ConfigError(ValueError):
    """Raised when configuration would weaken a required release boundary."""


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}
_PLACEHOLDER_SECRETS = {
    "replace-with-a-long-random-secret",
    "change-me",
    "changeme",
}
_PROVIDERS = {"mock", "ollama", "openai", "anthropic", "google", "gemini"}


def _boolean(env: Mapping[str, str], name: str, default: bool = False) -> bool:
    raw = str(env.get(name, str(default))).strip().lower()
    if raw in _TRUE:
        return True
    if raw in _FALSE:
        return False
    raise ConfigError(f"{name} must be a boolean value")


def _integer(
    env: Mapping[str, str],
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    try:
        value = int(str(env.get(name, default)).strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum}")
    return value


def _loopback_host(value: str) -> bool:
    if value.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def _validate_ollama_url(value: str, allow_remote: bool) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ConfigError("OLLAMA_BASE_URL must be an HTTP(S) URL")
    if not allow_remote and not _loopback_host(parsed.hostname):
        raise ConfigError("Remote Ollama endpoints require CARTER_ALLOW_REMOTE_OLLAMA=true")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ConfigError("OLLAMA_BASE_URL must not embed credentials, query, or fragment")
    return value.rstrip("/")


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Secret values are intentionally absent from public_dict."""

    provider: str
    default_model: str
    data_dir: Path
    log_level: str
    host: str
    port: int
    debug: bool
    enable_memory: bool
    enable_sensory_retention: bool
    session_idle_ttl_seconds: int
    allow_remote_ollama: bool
    ollama_base_url: str
    ollama_model: str
    flask_secret_key: str
    ephemeral_secret: bool
    csc_transcription_provider: str
    csc_interpretation_backend: str
    csc_ollama_model: str
    csc_buffer_seconds: int
    csc_buffer_max_events: int
    session_cookie_secure: bool

    def public_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model_configured": bool(self.default_model),
            "debug": self.debug,
            "bind_scope": "loopback" if _loopback_host(self.host) else "non_loopback",
            "memory_enabled": self.enable_memory,
            "durable_sensory_retention_enabled": False,
            "remote_ollama_allowed": self.allow_remote_ollama,
            "ollama_endpoint_scope": (
                "loopback"
                if _loopback_host(urlparse(self.ollama_base_url).hostname or "")
                else "remote"
            ),
            "transcription_provider": self.csc_transcription_provider,
            "interpretation_backend": self.csc_interpretation_backend,
            "secret_mode": "ephemeral" if self.ephemeral_secret else "configured",
            "session_cookie_secure": self.session_cookie_secure,
        }


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Load settings without reading a dotenv file or contacting any service."""

    source: Mapping[str, str] = os.environ if env is None else env
    provider = str(source.get("CARTER_PROVIDER", "mock")).strip().lower() or "mock"
    if provider not in _PROVIDERS:
        raise ConfigError(f"Unsupported CARTER_PROVIDER: {provider}")
    provider = "google" if provider == "gemini" else provider

    debug = _boolean(source, "CARTER_DEBUG", False)
    host = str(source.get("CARTER_HOST", "127.0.0.1")).strip() or "127.0.0.1"
    allow_public_bind = _boolean(source, "CARTER_ALLOW_PUBLIC_BIND", False)
    if not allow_public_bind and not _loopback_host(host):
        raise ConfigError("Non-loopback binding requires CARTER_ALLOW_PUBLIC_BIND=true")
    if debug and not _loopback_host(host):
        raise ConfigError("CARTER_DEBUG cannot be enabled on a non-loopback host")

    configured_secret = str(source.get("FLASK_SECRET_KEY", "")).strip()
    ephemeral_secret = (
        not configured_secret
        or configured_secret.lower() in _PLACEHOLDER_SECRETS
        or len(configured_secret) < 32
    )
    secret_key = secrets.token_urlsafe(48) if ephemeral_secret else configured_secret

    allow_remote_ollama = _boolean(source, "CARTER_ALLOW_REMOTE_OLLAMA", False)
    ollama_base_url = _validate_ollama_url(
        str(source.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).strip()
        or "http://127.0.0.1:11434",
        allow_remote_ollama,
    )

    provider_model_variable = {
        "ollama": "OLLAMA_MODEL",
        "openai": "OPENAI_MODEL",
        "anthropic": "ANTHROPIC_MODEL",
        "google": "GOOGLE_MODEL",
    }.get(provider)
    provider_model = (
        str(source.get(provider_model_variable, "")).strip() if provider_model_variable else ""
    )
    default_model = (
        str(source.get("CARTER_DEFAULT_MODEL", "")).strip()
        or provider_model
        or ("mock-v1" if provider == "mock" else "")
    )
    data_dir = Path(str(source.get("CARTER_DATA_DIR", "./data")).strip() or "./data").expanduser()

    transcription = (
        str(source.get("CSC_TRANSCRIPTION_PROVIDER", "disabled")).strip().lower() or "disabled"
    )
    if transcription not in {"disabled", "google", "gemini"}:
        raise ConfigError("CSC_TRANSCRIPTION_PROVIDER must be disabled or google")

    interpretation = str(source.get("CSC_INTERPRETATION_BACKEND", "mock")).strip().lower() or "mock"
    if interpretation not in {"mock", "ollama", "disabled"}:
        raise ConfigError("CSC_INTERPRETATION_BACKEND must be mock, ollama, or disabled")

    sensory_retention = _boolean(source, "CARTER_ENABLE_SENSORY_RETENTION", False)
    if sensory_retention:
        raise ConfigError(
            "CARTER_ENABLE_SENSORY_RETENTION is not implemented in public release 0.1.0"
        )

    return Settings(
        provider=provider,
        default_model=default_model,
        data_dir=data_dir,
        log_level=str(source.get("CARTER_LOG_LEVEL", "INFO")).strip().upper() or "INFO",
        host=host,
        port=_integer(source, "CARTER_PORT", 5000, minimum=1, maximum=65535),
        debug=debug,
        enable_memory=_boolean(source, "CARTER_ENABLE_MEMORY", False),
        enable_sensory_retention=sensory_retention,
        session_idle_ttl_seconds=_integer(
            source,
            "CARTER_SESSION_IDLE_TTL_SECONDS",
            3600,
            minimum=60,
            maximum=86400,
        ),
        allow_remote_ollama=allow_remote_ollama,
        ollama_base_url=ollama_base_url,
        ollama_model=str(source.get("OLLAMA_MODEL", "")).strip(),
        flask_secret_key=secret_key,
        ephemeral_secret=ephemeral_secret,
        csc_transcription_provider=("google" if transcription == "gemini" else transcription),
        csc_interpretation_backend=interpretation,
        csc_ollama_model=str(source.get("CSC_OLLAMA_MODEL", "")).strip(),
        csc_buffer_seconds=_integer(
            source,
            "CSC_ROLLING_BUFFER_SECONDS",
            60,
            minimum=5,
            maximum=3600,
        ),
        csc_buffer_max_events=_integer(
            source,
            "CSC_ROLLING_BUFFER_MAX_EVENTS",
            24,
            minimum=1,
            maximum=240,
        ),
        session_cookie_secure=_boolean(source, "CARTER_SESSION_COOKIE_SECURE", False),
    )
