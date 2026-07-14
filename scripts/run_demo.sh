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
export CARTER_PROVIDER="${CARTER_PROVIDER:-mock}"
export CARTER_HOST="${CARTER_HOST:-127.0.0.1}"
export CARTER_DEBUG="${CARTER_DEBUG:-false}"
exec "$PYTHON_BIN" -m carter.cli
