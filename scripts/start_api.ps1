Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")
Set-Location .\socializer-api

uvicorn socializer_api.app:app --reload --port 8000
