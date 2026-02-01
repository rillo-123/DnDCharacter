@echo off
REM Kill any existing Flask server first (idempotent)
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *backend*" >nul 2>&1
timeout /t 1 >nul
python "%~dp0activate-env.py" -Startserver -NoCheck %*
