# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir
$PythonBin = if ($env:PYTHON_BIN) {
    $env:PYTHON_BIN
} else {
    Join-Path $RootDir ".venv\Scripts\python.exe"
}
if (-not (Test-Path -LiteralPath $PythonBin)) {
    throw "Virtual environment not found. Run .\scripts\setup.ps1 first."
}
& $PythonBin -m pytest -m "not local_model and not cloud_provider and not slow" --cov=src --cov-report=term-missing
