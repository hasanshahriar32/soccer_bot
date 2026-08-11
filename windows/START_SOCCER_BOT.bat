@echo off
title "SOCCER BOT ROBOTICS SYSTEM"
cls
echo ====================================================================
echo             SOCCER BOT ROBOTICS SYSTEM (WINDOWS + WSL)
echo ====================================================================
echo.

cd /d "C:\Users\jatin\soccer_bot\windows"
"C:\Python314\python.exe" "launch_windows_hub.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================================================
    echo [ERROR] Launch script exited with code %ERRORLEVEL%.
    echo ====================================================================
    pause
) else (
    echo.
    echo ====================================================================
    echo System startup commands sent successfully.
    echo ====================================================================
    timeout /t 5 >nul
)
