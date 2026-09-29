@echo off
title SOCCER BOT - LIVE CAMERA WEB TELEOP AND CONTROLLER
color 0E
cls
echo ====================================================================
echo      SOCCER BOT - LIVE CAMERA WEB TELEOP AND CONTROLLER (PORT 5050)
echo ====================================================================
echo.
echo Launching Web Controller with Live Camera Feed and Robot Controls...
echo.

cd /d "C:\Users\jatin\soccer_bot"

set PYTHON_CMD=python
if exist "C:\Python314\python.exe" set PYTHON_CMD="C:\Python314\python.exe"
if exist "C:\Python312\python.exe" set PYTHON_CMD="C:\Python312\python.exe"

start "" http://localhost:5050
%PYTHON_CMD% "motor_control\web_teleop_server.py" %1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================================================
    echo [ERROR] Web teleop server exited with error code %ERRORLEVEL%.
    echo ====================================================================
    pause
)
