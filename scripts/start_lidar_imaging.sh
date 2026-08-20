#!/bin/bash
# ==========================================================
# Real-Time 2D LiDAR Imaging Launcher
# ==========================================================

echo "=================================================="
echo " 📡 YDLidar 2D Live Radar Imaging Launcher"
echo "=================================================="

# Check if /dev/ttyUSB0 exists
if [ ! -e /dev/ttyUSB0 ]; then
    echo "[ERROR] /dev/ttyUSB0 not found!"
    echo "Please ensure the YDLidar USB cable is firmly connected to this laptop."
    exit 1
fi

# Check permissions
if [ ! -r /dev/ttyUSB0 ] || [ ! -w /dev/ttyUSB0 ]; then
    echo "[INFO] Requesting permission for /dev/ttyUSB0..."
    sudo chmod 666 /dev/ttyUSB0
fi

echo "[INFO] Starting 2D LiDAR Imaging Display..."
python3 /home/sharmin/Desktop/iot/ydlidar-setup-docs/lidar_live_imaging.py
