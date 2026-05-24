@echo off
:: ========== Anti-Crash Guard Shell ==========
:: If launched by double-click, re-spawn under cmd /k so window never auto-closes
if /i not "%~1"=="--guarded" (
    start "Claude Monitor Launcher" cmd /k ""%~f0" --guarded"
    exit /b 0
)
:: ========== End Guard ==========

setlocal enabledelayedexpansion
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
if errorlevel 1 (
    echo   ERROR: cannot cd into script folder: %SCRIPT_DIR%
    goto :hold
)
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo   Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo   Failed to install dependencies
        goto :hold
    )
)
echo   Dependencies OK
echo.

:: 3. Start server
echo [3/3] Starting server...
if not exist "server.py" (
    echo   ERROR: server.py not found in %SCRIPT_DIR%
    goto :hold
)
start "Claude-Monitor-Server" cmd /k "python server.py"
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

:hold
echo.
echo Press any key to close this launcher window...
pause >nul

endlocal
