#!/bin/bash
# ====================================================================
# Soccer Bot Real-Time 2D LiDAR SLAM & Spatial Mapping Launcher
# ====================================================================

echo "=================================================="
echo " 🗺️ Starting Real-Time LiDAR SLAM & Mapping System"
echo "=================================================="

# Check if LiDAR USB exists
if [ ! -e /dev/ttyUSB0 ]; then
    echo "[ERROR] /dev/ttyUSB0 not found!"
    echo "Please ensure the YDLidar USB cable is firmly connected."
    exit 1
fi

# Ensure serial permissions
if [ ! -r /dev/ttyUSB0 ] || [ ! -w /dev/ttyUSB0 ]; then
    echo "[INFO] Granting permissions for /dev/ttyUSB0..."
    echo 1992 | sudo -S chmod 666 /dev/ttyUSB0
fi

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

echo "[INFO] Launching SLAM Toolbox, LiDAR Driver, TF & RViz2..."
ros2 launch soccer_slam soccer_slam_launch.py
