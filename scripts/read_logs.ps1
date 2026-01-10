Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path "$PSScriptRoot\..")

$logFiles = @(
  "admin-panel-temp/server_output.txt",
  "site/static_server.log",
  "site/static_server_2.log",
  "site/vibe.log",
  "site/vibe_kanban.log",
  "site/vibe_robust.log",
  "site/preview.log"
)

$existing = $logFiles | Where-Object { Test-Path $_ }

if ($existing.Count -eq 0) {
  Write-Host "No known log files found. Checked:"
  $logFiles | ForEach-Object { Write-Host "  - $_" }
  exit 0
}

foreach ($file in $existing) {
  Write-Host ""
  Write-Host "=== $file ==="
  Get-Content $file -Tail 200
}
