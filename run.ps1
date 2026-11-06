# Vaani Clinical (वाणी) PowerShell Startup Launcher
Set-Location -Path $PSScriptRoot

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  VAANI CLINICAL (वाणी) — REAL-TIME CLINICAL TELEPHONY & TRIAGE SYSTEM  " -ForegroundColor White
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python was not found in PATH. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Python detected at $($pythonCmd.Source)" -ForegroundColor Green
Write-Host "[OK] Starting Telemetry Server at http://127.0.0.1:8001 ..." -ForegroundColor Green
Write-Host ""

Start-Process "http://127.0.0.1:8001"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
