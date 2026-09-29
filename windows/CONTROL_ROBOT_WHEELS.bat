@echo off
title SOCCER BOT - MANUAL WHEEL REMOTE CONTROLLER
color 0B
cls
echo ====================================================================
echo             SOCCER BOT - MANUAL WHEEL REMOTE CONTROLLER
echo ====================================================================
echo.
echo Launching Universal Motor Control GUI (Wi-Fi + USB Serial)...
echo.

cd /d "C:\Users\jatin\soccer_bot"

set PYTHON_CMD=python
if exist "C:\Python314\python.exe" set PYTHON_CMD="C:\Python314\python.exe"
if exist "C:\Python312\python.exe" set PYTHON_CMD="C:\Python312\python.exe"

%PYTHON_CMD% "motor_control\gui_teleop.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================================================
    echo [ERROR] GUI exited with error code %ERRORLEVEL%.
    echo ====================================================================
    pause
)
