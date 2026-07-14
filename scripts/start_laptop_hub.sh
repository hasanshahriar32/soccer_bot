#!/bin/bash

# Source the ROS 2 workspace
source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

echo "Starting the ROS 2 Edge Hub..."

# Kill any existing processes
killall socat 2>/dev/null
pkill -f ydlidar_ros2_driver_node 2>/dev/null
pkill -f camera_hub 2>/dev/null


echo "Starting native Pi Camera TCP stream..."
sshpass -p "grammarpro" ssh -o StrictHostKeyChecking=no hasan@192.168.0.135 'pkill -f start_camera.sh; pkill -f rpicam-vid || true; nohup ~/start_camera.sh </dev/null >/dev/null 2>&1 &'
sleep 2

echo "Launching Camera Receiver Node..."
ros2 run soccer_vision camera_hub &

echo ""
echo "Hub is fully running! To visualize the data, open a NEW terminal and run:"
echo "source /opt/ros/jazzy/setup.bash"
echo "rviz2"
echo ""

# Keep the script running
wait
