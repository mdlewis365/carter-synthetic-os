# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir
$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
& $PythonBin -m venv .venv
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[dev]"
Write-Host "Environment ready. Run: .\scripts\run_demo.ps1"
