# Production Startup Script
Write-Host "Starting Socializer Production Pipeline..." -ForegroundColor Green

# 1. Check for .env
if (-not (Test-Path .env)) {
    Write-Host "Warning: .env file not found. Please create one." -ForegroundColor Yellow
    exit 1
}

# 2. Start API
Write-Host "Starting Socializer API..." -ForegroundColor Cyan
Start-Process -FilePath "powershell" -ArgumentList "-ExecutionPolicy, Bypass, -File, .\scripts\start_api.ps1" -WindowStyle Minimized

# 3. Start Content Worker
Write-Host "Starting Content Worker..." -ForegroundColor Cyan
# Using python directly assuming venv is active or default python has deps
# Better: use the venv from API?
$venvPython = "socializer-api\venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    # Fallback to loose python if venv not found there
    $venvPython = "python"
}
# Start in new window so we can see logs
Start-Process -FilePath $venvPython -ArgumentList "content_worker.py" 

# 4. Start Admin Panel
Write-Host "Starting Admin Panel..." -ForegroundColor Cyan
Set-Location "admin-panel-temp"
# npm run dev or start? dev for localhost usually better for now
npm run dev

# Note: This script waits for Admin Panel (npm) to exit. API and Worker run in background.
