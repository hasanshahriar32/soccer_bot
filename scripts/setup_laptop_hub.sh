#!/bin/bash
set -e

echo "Setting up the Laptop ROS 2 Hub..."

# Install socat and cv_bridge dependencies
sudo apt-get update
sudo apt-get install -y socat ros-jazzy-cv-bridge python3-opencv cmake build-essential

# Clone YDLidar packages into the workspace
cd /home/sharmin/Desktop/iot/soccer_bot/src
if [ ! -d "YDLidar-SDK" ]; then
    git clone https://github.com/YDLIDAR/YDLidar-SDK.git
fi
if [ ! -d "ydlidar_ros2_driver" ]; then
    git clone https://github.com/YDLIDAR/ydlidar_ros2_driver.git
fi

# Compile the native C++ YDLidar SDK on the laptop
echo "Compiling YDLidar SDK..."
cd YDLidar-SDK
mkdir -p build && cd build
cmake ..
make -j$(nproc)
sudo make install

# Compile the ROS 2 workspace
echo "Building the ROS 2 workspace..."
cd /home/sharmin/Desktop/iot/soccer_bot
source /opt/ros/jazzy/setup.bash
colcon build

echo "Laptop Hub setup complete!"
