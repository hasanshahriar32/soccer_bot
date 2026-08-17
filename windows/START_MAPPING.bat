@echo off
title SOCCER BOT - SLAM MAP BUILDER
color 0E
cls
echo ====================================================================
echo             SOCCER BOT - SLAM REAL-TIME MAP BUILDER
echo ====================================================================
echo.
echo [1/2] Launching slam_toolbox inside WSL (Ubuntu-22.04)...
wsl -d Ubuntu-22.04 -- bash -ic "source /opt/ros/humble/setup.bash && ros2 launch slam_toolbox online_async_launch.py"
echo.
echo ====================================================================
pause
