#!/bin/bash
set -e

# Source ROS 2 environment
source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash

echo "Starting Edge Node Sensors..."

# Start the Camera Node in the background
ros2 run v4l2_camera v4l2_camera_node --ros-args -p video_device:="/dev/video0" -p image_size:="[640,480]" &

# Start the Lidar Node
ros2 run ydlidar_ros2_driver ydlidar_ros2_driver_node --ros-args -p port:="/dev/ttyUSB0" -p frame_id:="laser_frame" -p baudrate:=115200 -p resolution_fixed:=true -p auto_reconnect:=true -p singlechannel:=true

wait
