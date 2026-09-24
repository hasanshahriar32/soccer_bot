#!/bin/bash
# ====================================================================
# Soccer Bot Real-Time 2D LiDAR SLAM & Spatial Mapping Launcher
# Supports:
#   Mode A: Direct USB connection on Laptop (/dev/ttyUSB0)
#   Mode B: Wireless TCP Bridge from Raspberry Pi (10.127.69.146:5000)
# ====================================================================

PI_IP="10.127.69.146"
PI_PORT="5000"
SOCAT_PID=""

cleanup() {
    echo ""
    echo "[INFO] Shutting down SLAM mapping session..."
    if [ -n "$SOCAT_PID" ]; then
        echo "[INFO] Stopping wireless LiDAR bridge..."
        kill "$SOCAT_PID" 2>/dev/null || true
    fi
    if [ -L /dev/ttyUSB0 ]; then
        echo 1992 | sudo -S rm -f /dev/ttyUSB0 2>/dev/null || true
    fi
    pkill -f "socat.*$PI_PORT" 2>/dev/null || true
    exit 0
}

trap cleanup INT TERM EXIT

echo "=================================================="
echo " 🗺️ Starting Real-Time LiDAR SLAM & Mapping System"
echo "=================================================="

# Check if LiDAR USB exists locally
if [ -e /dev/ttyUSB0 ] && [ ! -L /dev/ttyUSB0 ]; then
    echo "[INFO] Direct hardware LiDAR detected at /dev/ttyUSB0 (Laptop USB Mode)."
    echo 1992 | sudo -S chmod 666 /dev/ttyUSB0
else
    echo "[INFO] No local /dev/ttyUSB0. Checking for Wireless LiDAR on Pi ($PI_IP:$PI_PORT)..."
    if nc -z -w 3 "$PI_IP" "$PI_PORT" 2>/dev/null; then
        echo "[SUCCESS] Found active LiDAR TCP server on Raspberry Pi ($PI_IP:$PI_PORT)!"
        echo "[INFO] Establishing wireless PTY serial bridge..."
        
        rm -f /tmp/ttyLIDAR
        socat -d -d PTY,link=/tmp/ttyLIDAR,raw,echo=0,mode=666 TCP:"$PI_IP":"$PI_PORT" >/tmp/laptop_socat.log 2>&1 &
        SOCAT_PID=$!
        sleep 1.5

        if [ -e /tmp/ttyLIDAR ]; then
            echo 1992 | sudo -S ln -sf /tmp/ttyLIDAR /dev/ttyUSB0
            echo 1992 | sudo -S chmod 666 /dev/ttyUSB0
            echo "[SUCCESS] Wireless LiDAR successfully mapped to /dev/ttyUSB0!"
        else
            echo "[ERROR] Failed to establish /tmp/ttyLIDAR bridge."
            cat /tmp/laptop_socat.log
            exit 1
        fi
    else
        echo "[ERROR] Could not connect to LiDAR on Raspberry Pi ($PI_IP:$PI_PORT) or local USB!"
        echo "Please ensure Raspberry Pi is powered on, connected to the hotspot, or LiDAR is plugged into laptop."
        exit 1
    fi
fi

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

echo "[INFO] Launching SLAM Toolbox, LiDAR Driver, TF, Phone Gyro & RViz2..."
ros2 launch soccer_slam soccer_slam_launch.py
