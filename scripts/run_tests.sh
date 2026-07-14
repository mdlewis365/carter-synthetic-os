#!/usr/bin/env sh
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  printf '%s\n' "Virtual environment not found. Run ./scripts/setup.sh first." >&2
  exit 1
fi
exec "$PYTHON_BIN" -m pytest \
  -m "not local_model and not cloud_provider and not slow" \
  --cov=src --cov-report=term-missing
