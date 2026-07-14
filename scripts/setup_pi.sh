#!/bin/bash
# Raspberry Pi Setup Script for Soccer Bot
# OS Requirement: Ubuntu Server 24.04 (ARM64)
# Note: Run this script on the Raspberry Pi after fresh OS installation.

echo "Starting Raspberry Pi Soccer Bot Setup..."

# 1. Update the system
echo "Updating packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install ROS 2 Jazzy Jalisco
echo "Installing ROS 2 Jazzy..."
sudo apt-get install -y software-properties-common curl
sudo add-apt-repository universe -y
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt-get update
sudo apt-get install -y ros-jazzy-ros-base python3-colcon-common-extensions

# 3. Install Computer Vision Dependencies (OpenCV)
echo "Installing Computer Vision dependencies..."
sudo apt-get install -y python3-opencv python3-numpy python3-pip

# 4. Install Hardware/GPIO libraries for motor control
echo "Installing Hardware Control dependencies..."
sudo apt-get install -y python3-gpiozero python3-rpi.gpio

# 5. Install Lidar dependencies (SWIG, CMake)
echo "Installing Lidar SDK dependencies..."
sudo apt-get install -y cmake swig python3-dev

# 6. Setup ROS workspace structure
echo "Creating ROS 2 Workspace..."
mkdir -p ~/soccer_bot_ws/src
cd ~/soccer_bot_ws/src

# 7. Clone YDLidar ROS 2 Driver
echo "Cloning YDLidar ROS 2 Driver..."
git clone https://github.com/YDLIDAR/ydlidar_ros2_driver.git

echo "Setup Complete! Please source ROS 2 using: source /opt/ros/jazzy/setup.bash"
echo "Then build your workspace using: cd ~/soccer_bot_ws && colcon build"
