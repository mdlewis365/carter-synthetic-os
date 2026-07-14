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
if (-not $env:CARTER_PROVIDER) { $env:CARTER_PROVIDER = "mock" }
if (-not $env:CARTER_HOST) { $env:CARTER_HOST = "127.0.0.1" }
if (-not $env:CARTER_DEBUG) { $env:CARTER_DEBUG = "false" }
& $PythonBin -m carter.cli
