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
    echo "[INFO] Shutting down full system session..."
    # 1. Stop local web teleop & autopilot
    pkill -f "web_teleop_server.py" 2>/dev/null || true

    # 2. Stop robot motors immediately for safety
    curl -s -X POST -H "Content-Type: application/json" -d '{"action":"S"}' http://127.0.0.1:5050/api/drive 2>/dev/null || true

    # 3. Stop wireless LiDAR serial bridge
    if [ -n "$SOCAT_PID" ]; then
        echo "[INFO] Stopping wireless LiDAR bridge..."
        kill "$SOCAT_PID" 2>/dev/null || true
    fi
    if [ -L /dev/ttyUSB0 ]; then
        echo 1992 | sudo -S rm -f /dev/ttyUSB0 2>/dev/null || true
    fi
    pkill -f "socat.*$PI_PORT" 2>/dev/null || true

    # 4. Stop Pi Screen HUD on Raspberry Pi
    echo "[INFO] Stopping Pi screen HUD on robot..."
    sshpass -p "grammarpro" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 hasan@"$PI_IP" 'pkill -f pi_screen_hud.py' 2>/dev/null || true

    echo "[INFO] Full system shutdown complete."
    exit 0
}

trap cleanup INT TERM EXIT

echo "=========================================================="
echo " 🤖 SOCCER BOT - UNIFIED FULL SYSTEM AUTONOMOUS LAUNCHER"
echo "=========================================================="

# 1. Start Mobile Web Controller & Autopilot Server immediately
fuser -k 5050/tcp 2>/dev/null || true
python3 /home/sharmin/Desktop/iot/soccer_bot/motor_control/web_teleop_server.py >/tmp/web_teleop.log 2>&1 &
echo "=========================================================="
echo " 📱 MOBILE CONTROLLER READY: http://192.168.0.122:5050"
echo " Open this link on your phone browser right now!"
echo "=========================================================="

# Check if LiDAR USB exists locally
if [ -e /dev/ttyUSB0 ] && [ ! -L /dev/ttyUSB0 ]; then
    echo "[INFO] Direct hardware LiDAR detected at /dev/ttyUSB0 (Laptop USB Mode)."
    echo 1992 | sudo -S chmod 666 /dev/ttyUSB0
else
    echo "[INFO] Checking connection to Raspberry Pi ($PI_IP)..."
    FOUND=0
    for attempt in $(seq 1 100); do
        if ping -c 1 -W 1 "$PI_IP" >/dev/null 2>&1; then
            FOUND=1
            break
        fi
        echo -ne "\r[WAIT] Waiting for Raspberry Pi ($PI_IP) on Wi-Fi... [${attempt}/100]  "
        sleep 2
    done
    echo ""

    if [ "$FOUND" -eq 1 ]; then
        echo "[SUCCESS] Raspberry Pi is online at $PI_IP!"

        # Ensure all Pi Onboard Services & Hardware are active
        echo "[INFO] Initializing Pi onboard services (Camera, Motors, LiDAR, Screen HUD)..."
        sshpass -p "grammarpro" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 hasan@"$PI_IP" bash -s << 'EOF'
            # 1. Motor Server on port 9000
            if ! pgrep -f "motor_server.py" >/dev/null; then
                echo "[PI] Starting Motor Server on port 9000..."
                nohup /usr/bin/python3 -u /home/hasan/motor_server.py </dev/null >/tmp/motor_server.log 2>&1 & disown
            fi

            # 2. Camera & Live Ball Detector on port 8000
            if ! pgrep -f "detect_live_picamera2.py" >/dev/null; then
                echo "[PI] Starting Camera Server on port 8000..."
                nohup /home/hasan/ball_detector_pi/pi_inference/venv/bin/python3 -u /home/hasan/ball_detector_pi/pi_inference/detect_live_picamera2.py </dev/null >/tmp/camera.log 2>&1 & disown
            fi

            # 3. YDLidar DTR-Powered TCP Bridge on port 5000
            echo "[PI] Ensuring YDLidar DTR Bridge on port 5000..."
            pkill -f "socat.*5000" 2>/dev/null || true
            if ! pgrep -f "lidar_bridge.py" >/dev/null; then
                nohup python3 -u /home/hasan/lidar_bridge.py </dev/null >/tmp/lidar_bridge.log 2>&1 & disown
            fi
EOF

        # Deploy and launch Pi Screen HUD & LiDAR Bridge on Raspberry Pi
        echo "[INFO] Updating and launching SLAM HUD on Raspberry Pi Screen..."
        sshpass -p "grammarpro" scp -o StrictHostKeyChecking=no -o ConnectTimeout=5 /home/sharmin/Desktop/iot/soccer_bot/scripts/lidar_bridge.py /home/sharmin/Desktop/iot/soccer_bot/scripts/pi_screen_hud.py hasan@"$PI_IP":/home/hasan/ 2>/dev/null || true
        sshpass -p "grammarpro" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 hasan@"$PI_IP" 'pkill -f pi_screen_hud.py 2>/dev/null || true; DISPLAY=:0.0 XAUTHORITY=/home/hasan/.Xauthority nohup python3 -u /home/hasan/pi_screen_hud.py </dev/null >/tmp/pi_hud.log 2>&1 & disown' || true
        echo "[SUCCESS] Raspberry Pi Screen HUD running!"

        # Wait for LiDAR TCP port 5000
        for l_attempt in $(seq 1 10); do
            if nc -z -w 1 "$PI_IP" "$PI_PORT" 2>/dev/null; then
                break
            fi
            sleep 1
        done

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
            echo "[WARN] Could not establish /tmp/ttyLIDAR bridge (LiDAR may be offline)."
        fi
    else
        echo "[WARN] Raspberry Pi ($PI_IP) did not respond in time."
        echo "Mobile Web App is running; Pi services will auto-connect when Pi joins Wi-Fi."
    fi
fi

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

# CycloneDDS Configuration (Bound strictly to wlp2s0 Wi-Fi interface, never docker0 or loopback)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=/home/sharmin/Desktop/iot/soccer_bot/scripts/cyclonedds.xml
export ROS_DOMAIN_ID=0

echo "[INFO] Launching SLAM Toolbox, LiDAR Driver, TF, Phone Gyro & RViz2..."
ros2 launch soccer_slam soccer_slam_launch.py || true
