@echo off
title START SOCCER BOT SYSTEM - WINDOWS & WSL
cls
echo ====================================================================
echo             SOCCER BOT ROBOTICS SYSTEM (WINDOWS + WSL)
echo ====================================================================
echo.

set PYTHON_EXE=python
if exist "C:\Python312\python.exe" set PYTHON_EXE=C:\Python312\python.exe

"%PYTHON_EXE%" "%~dp0launch_windows_hub.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================================================
    echo [ERROR] System launch encountered an error (Exit Code: %ERRORLEVEL%).
    echo ====================================================================
    pause
) else (
    echo.
    echo ====================================================================
    echo System startup commands sent successfully.
    echo Window closing automatically in 5 seconds...
    echo ====================================================================
    ping -n 5 127.0.0.1 >nul
)
