@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Claude Code Monitor - Startup

echo ========================================
echo   Claude Code Monitor
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"

:: 1. Check port 5555
echo [1/3] Checking port 5555...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5555 " ^| findstr "LISTENING"') do (
    echo   Clearing port 5555 ^(PID: %%a^)...
    taskkill /F /PID %%a >nul 2>&1
)
echo   Port check done
echo.

:: 2. Check dependencies
echo [2/3] Checking dependencies...
cd /d "%SCRIPT_DIR%"
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo   Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo   Failed to install dependencies
        pause
        exit /b 1
    )
)
echo   Dependencies OK
echo.

:: 3. Start server
echo [3/3] Starting server...
cd /d "%SCRIPT_DIR%"
if not exist "server.py" (
    echo   Error: server.py not found
    pause
    exit /b 1
)
start "Claude-Monitor" cmd /k "cd /d "%SCRIPT_DIR%" && python server.py"
echo.

:: Open browser
echo ========================================
echo   Claude Code Monitor started!
echo   Dashboard: http://localhost:5555
echo ========================================
echo.

echo Opening browser...
timeout /t 3 /nobreak >nul
start "" "http://localhost:5555"

echo Press any key to close this window...
pause >nul

endlocal
