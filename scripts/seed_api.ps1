Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")
Set-Location .\socializer-api

python .\seed_socializer_api.py
