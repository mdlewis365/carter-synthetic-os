#!/usr/bin/env sh
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"${PYTHON_BIN}" -m venv .venv
"$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$ROOT_DIR/.venv/bin/python" -m pip install -e ".[dev]"
printf '%s\n' "Environment ready. Run: ./scripts/run_demo.sh"
