Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")
Set-Location .\admin-panel-temp

$env:NODE_ENV = "development"
npm run dev
