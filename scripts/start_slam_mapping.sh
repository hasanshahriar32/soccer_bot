#!/bin/bash
# ====================================================================
# Soccer Bot Real-Time 2D LiDAR SLAM & Spatial Mapping Launcher
# Supports:
#   Mode A: Direct USB connection on Laptop (/dev/ttyUSB0)
#   Mode B: Wireless TCP Bridge from Raspberry Pi (192.168.0.135:5000)
# ====================================================================

PI_IP="192.168.0.135"
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
    pkill -f "web_teleop_server.py" 2>/dev/null || true
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
    echo "[INFO] Checking for Wireless LiDAR on Pi ($PI_IP:$PI_PORT)..."
    FOUND=0
    for attempt in $(seq 1 30); do
        if nc -z -w 2 "$PI_IP" "$PI_PORT" 2>/dev/null; then
            FOUND=1
            break
        fi
        echo -ne "\r[WAIT] Waiting for Raspberry Pi ($PI_IP:$PI_PORT) to boot... [${attempt}/30]  "
        sleep 2
    done
    echo ""

    if [ "$FOUND" -eq 1 ]; then
        echo "[SUCCESS] Found active LiDAR TCP server on Raspberry Pi ($PI_IP:$PI_PORT)!"
        echo "[INFO] Establishing wireless PTY serial bridge..."
        
        rm -f /tmp/ttyLIDAR
        # Persistent auto-reconnecting wireless serial bridge
        (
            while true; do
                socat -d -d PTY,link=/tmp/ttyLIDAR,raw,echo=0,mode=666 TCP:"$PI_IP":"$PI_PORT",retry=999,interval=1 >>/tmp/laptop_socat.log 2>&1
                sleep 1
            done
        ) &
        SOCAT_PID=$!
        sleep 2

        if [ -e /tmp/ttyLIDAR ]; then
            echo 1992 | sudo -S ln -sf /tmp/ttyLIDAR /dev/ttyUSB0
            echo 1992 | sudo -S chmod 666 /tmp/ttyLIDAR /dev/ttyUSB0 2>/dev/null || true
            echo "[SUCCESS] Wireless LiDAR successfully mapped to /dev/ttyUSB0!"
        else
            echo "[ERROR] Failed to establish /tmp/ttyLIDAR bridge."
            cat /tmp/laptop_socat.log
            exit 1
        fi
    else
        echo "[ERROR] Raspberry Pi ($PI_IP:$PI_PORT) did not respond in time."
        echo "Please verify Raspberry Pi is powered on and connected to the Wi-Fi."
        exit 1
    fi
fi

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

# Start Mobile Web Teleop & Autopilot Server (Port 5050)
pkill -f "web_teleop_server.py" 2>/dev/null || true
python3 /home/sharmin/Desktop/iot/soccer_bot/motor_control/web_teleop_server.py >/tmp/web_teleop.log 2>&1 &
echo "=================================================="
echo " 📱 MOBILE CONTROLLER: http://192.168.0.122:5050"
echo " Open the above link on your phone browser!"
echo "=================================================="

echo "[INFO] Launching SLAM Toolbox, LiDAR Driver, TF, Phone Gyro & RViz2..."
ros2 launch soccer_slam soccer_slam_launch.py
