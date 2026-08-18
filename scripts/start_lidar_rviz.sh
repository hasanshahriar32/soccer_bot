#!/bin/bash
# ==========================================================
# Real-Time LiDAR ROS 2 Driver & RViz2 Viewer Launcher
# ==========================================================

echo "=================================================="
echo " 📡 Launching YDLidar ROS 2 Driver & RViz2 Viewer"
echo "=================================================="

# Check if /dev/ttyUSB0 exists
if [ ! -e /dev/ttyUSB0 ]; then
    echo "[ERROR] /dev/ttyUSB0 not found!"
    echo "Please ensure the YDLidar USB cable is plugged into this laptop."
    exit 1
fi

# Check permissions
if [ ! -r /dev/ttyUSB0 ] || [ ! -w /dev/ttyUSB0 ]; then
    echo "[INFO] Granting permissions on /dev/ttyUSB0..."
    sudo chmod 666 /dev/ttyUSB0
fi

# Source ROS 2 Jazzy & Workspace
source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

echo "[INFO] Launching YDLidar ROS 2 Driver and RViz2..."
ros2 launch ydlidar_ros2_driver ydlidar_launch_view.py
