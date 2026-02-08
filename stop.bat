@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Claude Code Monitor - Stop

echo ========================================
echo   Stopping Claude Code Monitor...
echo ========================================
echo.

:: Kill by port
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5555 " ^| findstr "LISTENING"') do (
    echo   Stopping process ^(PID: %%a^)...
    taskkill /F /PID %%a >nul 2>&1
)

:: Kill by window title
taskkill /FI "WINDOWTITLE eq Claude-Monitor*" /F >nul 2>&1

echo.
echo   Stopped.
echo.
pause

endlocal
