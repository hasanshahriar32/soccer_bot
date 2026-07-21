#!/bin/bash
# test_cmd_vel.sh
# Tests ROS 2 /cmd_vel topic movement commands for the Soccer Bot

source /opt/ros/jazzy/setup.bash

echo "=========================================="
echo " ROS 2 /cmd_vel Motor Control Test"
echo "=========================================="

echo "Sending Forward command (linear.x = 0.5)..."
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.0}}"
sleep 2

echo "Sending Stop command..."
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
sleep 1

echo "Sending Backward command (linear.x = -0.5)..."
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: -0.5}, angular: {z: 0.0}}"
sleep 2

echo "Sending Stop command..."
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
sleep 1

echo "Sending Left Turn command (angular.z = 0.5)..."
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.5}}"
sleep 1.5

echo "Sending Stop command..."
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
sleep 1

echo "Sending Right Turn command (angular.z = -0.5)..."
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {-0.5}}"
sleep 1.5

echo "Sending final Stop command..."
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"

echo "Test complete!"
