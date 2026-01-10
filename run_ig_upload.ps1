# Instagram Upload Script for Windows
# Run from the socializer project root directory
#
# Usage:
#   .\run_ig_upload.ps1 <video_path> "<caption>"
#
# Example:
#   .\run_ig_upload.ps1 "C:\Videos\my_reel.mp4" "Check out this video! #viral"
#
# Prerequisites:
#   1. Copy .env.example to .env and fill in IG_USERNAME and IG_PASSWORD
#   2. Run interactive login first: python examples\instagram_interactive.py

param(
    [Parameter(Mandatory = $true)]
    [string]$VideoPath,
    
    [Parameter(Mandatory = $false)]
    [string]$caption = ""$Caption""
)

# Load environment variables from .env file
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Host "✅ Loaded environment from .env" -ForegroundColor Green
}
else {
    Write-Host "⚠️ No .env file found. Using system environment variables." -ForegroundColor Yellow
}

# Validate video path
if (-not (Test-Path $VideoPath)) {
    Write-Host "❌ Error: Video file not found: $VideoPath" -ForegroundColor Red
    exit 1
}

# Check if credentials are configured
$username = $env:IG_USERNAME
$password = $env:IG_PASSWORD

if (-not $username -or -not $password) {
    Write-Host "❌ Error: IG_USERNAME and IG_PASSWORD must be set in .env file" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           Instagram Upload Script                  ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📹 Video: $VideoPath" -ForegroundColor White
Write-Host "📝 Caption: $Caption" -ForegroundColor White
Write-Host "👤 Account: $username" -ForegroundColor White
Write-Host ""

# Change to project directory
$projectRoot = $PSScriptRoot
Set-Location $projectRoot

# Run the upload script
Write-Host "🚀 Starting upload..." -ForegroundColor Yellow
Write-Host ""

$pythonScript = @"
import sys
import os

# Add project root to path
sys.path.insert(0, '$($projectRoot -replace '\\', '/')')

from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator
from radar.ig_config import IG_SESSION_DIR, get_ig_username, get_ig_password

video_path = r'$VideoPath'
caption = ""$Caption""', '\"')"

print(f"Loading session from {IG_SESSION_DIR}...")

with BrowserManager() as manager:
    automator = InstagramAutomator(manager, user_data_dir=IG_SESSION_DIR)
    
    # Try session-based login first
    print("Attempting login...")
    if not automator.login(get_ig_username(), get_ig_password(), headless=True):
        print(f"❌ Login failed: {automator.last_error}")
        sys.exit(1)
    
    print("✅ Logged in successfully")
    print(f"📤 Uploading video: {video_path}")
    
    success = automator.upload_video(
        file_path=video_path,
        caption=caption
    )
    
    if success:
        print("✅ Upload completed successfully!")
        sys.exit(0)
    else:
        print(f"❌ Upload failed: {automator.last_error}")
        sys.exit(1)
"@

# Execute Python script
python -c $pythonScript

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "✅ Upload completed successfully!" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "❌ Upload failed. Check the error messages above." -ForegroundColor Red
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Red
    exit 1
}
