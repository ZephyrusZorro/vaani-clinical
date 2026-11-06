@echo off
setlocal
cd /d "%~dp0"
title Vaani Clinical Telemetry & Triage Workstation

echo ========================================================================
echo   VAANI CLINICAL (वाणी) - REAL-TIME CLINICAL VOICE & TRIAGE PLATFORM
echo ========================================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

echo [OK] Launching Vaani Clinical Telemetry Server on http://127.0.0.1:8001 ...
echo [INFO] Press Ctrl+C in this terminal window to stop the service.
echo.

start "" http://127.0.0.1:8001

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload

pause
