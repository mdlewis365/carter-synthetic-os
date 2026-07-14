# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
"""Public Synthetic Operating System interfaces.

Importing :mod:`sos` performs no network, provider, or storage initialization.
"""

from .registry import ComponentDescriptor, SubsystemRegistry, default_registry

__all__ = ["ComponentDescriptor", "SubsystemRegistry", "default_registry"]

__version__ = "0.1.0"
