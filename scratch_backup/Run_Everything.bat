@echo off
title START SOCCER BOT SYSTEM
echo ==================================================
echo    LAUNCHING SOCCER BOT SENSORS, CAM & RVIZ
echo ==================================================
python C:\Users\taufi\Desktop\soccer_bot\launch_all_system.py
echo.
echo All processes initiated. You can close this window.
ping -n 5 127.0.0.1 >nul
