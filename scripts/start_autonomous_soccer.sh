#!/bin/bash
# start_autonomous_soccer.sh
# Complete Master All-In-One Launcher for Autonomous Soccer Bot

source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

echo "=========================================="
echo " Starting Full Autonomous Soccer System..."
echo "=========================================="

# 1. Clean up old laptop processes
killall socat 2>/dev/null
pkill -f ydlidar_ros2_driver_node 2>/dev/null
pkill -f camera_hub 2>/dev/null
pkill -f motor_bridge_node 2>/dev/null
pkill -f ball_tracker_node 2>/dev/null
pkill -f soccer_brain_node 2>/dev/null

# 2. Launch persistent Pi Camera and Motor Edge Server
echo "Launching Raspberry Pi Camera Stream & Motor Server..."
sshpass -p "grammarpro" ssh -o StrictHostKeyChecking=no hasan@192.168.0.135 'pkill -f rpicam-vid || true; pkill -f start_camera || true; pkill -f motor_edge_server || true; nohup ~/start_camera.sh >/dev/null 2>&1 & nohup python3 -u ~/soccer_bot/src/arduino/motor_driver/motor_edge_server.py >/tmp/motor_server.log 2>&1 & sleep 2'
sleep 2

# 3. Launch Laptop ROS 2 Communication & Robot State Nodes
echo "Launching Camera Receiver Node (/image_raw)..."
ros2 run soccer_vision camera_hub &

echo "Launching 3D URDF Robot Model..."
ros2 run robot_state_publisher robot_state_publisher /home/sharmin/Desktop/iot/soccer_bot/scripts/robot.urdf &

echo "Launching Motor Bridge Node (/cmd_vel -> Pi)..."
python3 /home/sharmin/Desktop/iot/soccer_bot/src/arduino/motor_driver/motor_bridge_node.py &
sleep 3

# 4. Launch Vision Ball Tracker & Autonomous Core Brain
echo "Launching Universal Vision Ball Tracker..."
python3 /home/sharmin/Desktop/iot/soccer_bot/src/soccer_vision/soccer_vision/ball_tracker_node.py &

echo "Launching Autonomous Core Brain Decision Engine..."
python3 /home/sharmin/Desktop/iot/soccer_bot/src/core_brain/soccer_brain_node.py &

echo ""
echo "=================================================="
echo " ALL SYSTEMS LIVE & CONNECTED! Soccer Bot seeking!"
echo "=================================================="
echo "Press Ctrl+C to stop."
echo ""

wait
