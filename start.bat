@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title Vaani Clinical Telemetry & Triage Workstation

echo ========================================================================
echo   VAANI CLINICAL -- REAL-TIME CLINICAL VOICE & TRIAGE PLATFORM
echo ========================================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

python run_server.py
pause
