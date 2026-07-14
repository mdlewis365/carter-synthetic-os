# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Lazy model-provider boundary.

``create_provider`` constructs adapters but never contacts a provider. Optional
SDKs are imported only when their adapter is invoked.
"""

from .base import ModelProvider, ModelRequest, ModelResponse, ProviderError
from .registry import ProviderRegistry, available_providers, create_provider

__all__ = [
    "ModelProvider",
    "ModelRequest",
    "ModelResponse",
    "ProviderError",
    "ProviderRegistry",
    "available_providers",
    "create_provider",
]
