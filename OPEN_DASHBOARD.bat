@echo off
title "SOCCER BOT - LIVE SENSOR DASHBOARD"
cls
echo ====================================================================
echo             STARTING SOCCER BOT LIVE DASHBOARD
echo ====================================================================
echo.
cd /d "C:\Users\jatin\soccer_bot"
"C:\Python314\python.exe" "scripts\soccer_bot_dashboard.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Dashboard exited with code %ERRORLEVEL%.
    pause
)
