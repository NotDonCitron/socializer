Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")

Set-Location .\admin-panel-temp
npm run check

Set-Location ..
python -m pytest tests/ -v -m "not slow"
