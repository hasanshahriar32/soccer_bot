#!/bin/bash
# start_laptop_hub.sh
# Master launcher for Laptop ROS 2 Hub (Camera, URDF Model, Pi Motor Server & Motor Bridge)

source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

echo "=========================================="
echo " Launching Laptop ROS 2 Communication Hub..."
echo "=========================================="

# 1. Clean up old processes
killall socat 2>/dev/null
pkill -f camera_hub 2>/dev/null
pkill -f motor_bridge_node 2>/dev/null

# 2. Trigger Pi Camera stream & Motor Edge Server over SSH
echo "Initializing Pi Camera stream & Motor Server..."
sshpass -p "grammarpro" ssh -o StrictHostKeyChecking=no hasan@192.168.0.135 'pkill -f rpicam-vid || true; pkill -f start_camera || true; pkill -f motor_edge_server || true; nohup ~/start_camera.sh >/dev/null 2>&1 & nohup python3 -u ~/soccer_bot/src/arduino/motor_driver/motor_edge_server.py >/tmp/motor_server.log 2>&1 & sleep 2'
sleep 2

# 3. Launch Camera Receiver Node
echo "Launching Camera Receiver Node (/image_raw)..."
ros2 run soccer_vision camera_hub &

# 4. Launch 3D Robot State Publisher
echo "Launching 3D URDF Robot Model..."
ros2 run robot_state_publisher robot_state_publisher /home/sharmin/Desktop/iot/soccer_bot/scripts/robot.urdf &

# 5. Launch ROS 2 Motor Bridge Node
echo "Launching Motor Bridge Node (/cmd_vel -> Pi)..."
python3 /home/sharmin/Desktop/iot/soccer_bot/src/arduino/motor_driver/motor_bridge_node.py &

echo ""
echo "Laptop ROS 2 Hub is LIVE and connected to Pi!"
echo "Press Ctrl+C to stop."
echo ""

wait
