@echo off
title Launch ROS 2 RViz GUI

tasklist /FI "IMAGENAME eq vcxsrv.exe" 2>NUL | find /I /N "vcxsrv.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo Starting VcXsrv X-Server...
    start "" "C:\Program Files\VcXsrv\vcxsrv.exe" :0 -ac -multiwindow -clipboard -wgl
    ping -n 4 127.0.0.1 >nul
)

echo Starting ROS 2 RViz GUI...
wsl -d Ubuntu -- bash -c "export DISPLAY=$(ip route show default | awk '{print $3}'):0; export QT_QPA_PLATFORM=xcb; export LIBGL_ALWAYS_SOFTWARE=1; source /opt/ros/jazzy/setup.bash; rviz2 -d /mnt/c/Users/taufi/Desktop/soccer_bot/soccer_bot.rviz"
