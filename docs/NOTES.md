# Project Notes: Autonomous Soccer Bot

## 📅 Project Log
*   **Hardware Setup**: YDLidar is connected to `/dev/ttyUSB0` at 115200 baud. Tested and verified working.
*   **Software Stack**: Transitioning to **ROS 2 Jazzy Jalisco** (Ubuntu 24.04 / Linux Mint 22.2) to properly handle robot navigation, sensor fusion, and computer vision.
*   **Workspace Created**: `/home/sharmin/Desktop/iot/soccer_bot` has been scaffolded.

## 🛠️ Installation & Setup Commands
Because ROS 2 requires administrator privileges (`sudo`), **these commands must be run manually by the user in the terminal**. 

**1. Install ROS 2 on Laptop:**
```bash
cd /home/sharmin/Desktop/iot/soccer_bot
chmod +x scripts/install_ros2_laptop.sh
./scripts/install_ros2_laptop.sh
```

**2. Compile the Workspace (After ROS 2 is installed):**
```bash
cd /home/sharmin/Desktop/iot/soccer_bot
colcon build
source install/setup.bash
```

## 🧠 Current Architecture
*   **Vision Node (`soccer_vision`)**: Ready to be wrapped in ROS 2. Currently contains the OpenCV HSV color tracking logic.
*   **Navigation Node (`lidar_navigation`)**: Contains the reactive obstacle avoidance math.
*   **Core Brain (`core_brain`)**: A finite state machine to switch between Searching, Chasing, and Avoiding.
*   **Motor Control (`motor_control`)**: Hardware abstraction for L298N motor driver using `gpiozero`.
