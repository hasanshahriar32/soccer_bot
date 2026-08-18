@echo off
title SOCCER BOT ROBOTICS SYSTEM
cls
echo ====================================================================
echo             SOCCER BOT ROBOTICS SYSTEM (WINDOWS + WSL)
echo ====================================================================
echo.

cd /d "%~dp0"

set PYTHON_EXE=python
if exist "C:\Python312\python.exe" set PYTHON_EXE="C:\Python312\python.exe"

%PYTHON_EXE% "%~dp0launch_windows_hub.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================================================
    echo [ERROR] Launch script exited with code %ERRORLEVEL%.
    echo ====================================================================
    pause
) else (
    echo.
    echo ====================================================================
    echo All processes initiated successfully.
    echo You may close this window.
    echo ====================================================================
    ping -n 5 127.0.0.1 >nul
)
