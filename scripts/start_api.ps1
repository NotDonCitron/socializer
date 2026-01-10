Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")
Set-Location .\socializer-api

uvicorn app.main:app --reload --port 8000
