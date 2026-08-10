@echo off
title START SOCCER BOT SYSTEM - WINDOWS & WSL
cls
echo ====================================================================
echo             SOCCER BOT ROBOTICS SYSTEM (WINDOWS + WSL)
echo ====================================================================
echo.
python "%~dp0launch_windows_hub.py"
echo.
echo ====================================================================
echo System startup commands sent successfully.
echo You may close this window.
echo ====================================================================
ping -n 5 127.0.0.1 >nul
