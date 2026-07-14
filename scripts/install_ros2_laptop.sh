#!/bin/bash
# Script to install ROS 2 Jazzy on Linux Mint 22.2 (Ubuntu 24.04 based)
# This will prepare your laptop for ROS 2 development.

echo "Setting up locale..."
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

echo "Enabling Ubuntu Universe repository..."
sudo apt install software-properties-common
sudo add-apt-repository universe

echo "Adding ROS 2 GPG key..."
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "Adding ROS 2 repository..."
# Linux Mint 22.2 uses the 'noble' Ubuntu base
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

echo "Updating apt repository..."
sudo apt update
sudo apt upgrade -y

echo "Installing ROS 2 Jazzy Desktop (Includes RViz, GUI tools)..."
sudo apt install ros-jazzy-desktop -y

echo "Installing ROS 2 development tools..."
sudo apt install -y python3-colcon-common-extensions python3-rosdep python3-vcstool

echo "Initializing rosdep..."
sudo rosdep init
rosdep update

echo "Environment setup..."
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source /opt/ros/jazzy/setup.bash

echo "ROS 2 Jazzy installation is complete on your laptop!"
echo "Please close this terminal and open a new one to apply changes."
