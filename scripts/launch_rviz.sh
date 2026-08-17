#!/bin/bash
# ============================================================
# Soccer Bot RViz2 Master Launcher for WSL2 + VcXsrv
# ============================================================

# 1. Clean up old background processes
pkill -9 -f lidar_hub_node 2>/dev/null || true
pkill -9 -f camera_hub_node 2>/dev/null || true
pkill -9 -f robot_state_publisher 2>/dev/null || true
pkill -9 -f static_transform_publisher 2>/dev/null || true
pkill -9 -f path_publisher 2>/dev/null || true
pkill -9 -f rviz2 2>/dev/null || true

# 2. X11 Display Settings (VcXsrv listens on localhost :0)
export DISPLAY=127.0.0.1:0
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3

source /opt/ros/humble/setup.bash

echo "==========================================================="
echo "   Launching RViz2 GUI on DISPLAY: $DISPLAY"
echo "==========================================================="

python3 /mnt/c/Users/jatin/soccer_bot/src/soccer_vision/soccer_vision/lidar_hub_node.py &
python3 /mnt/c/Users/jatin/soccer_bot/src/soccer_vision/soccer_vision/camera_hub_node.py &
python3 /mnt/c/Users/jatin/soccer_bot/scripts/path_publisher.py &
ros2 run robot_state_publisher robot_state_publisher /mnt/c/Users/jatin/soccer_bot/scripts/robot.urdf &
ros2 run tf2_ros static_transform_publisher --x 0 --y -0.019 --z 0.09 --roll 0 --pitch 0 --yaw 0 --frame-id base_link --child-frame-id laser_frame &
ros2 run tf2_ros static_transform_publisher --x 0.08 --y 0 --z 0.05 --roll 0 --pitch 0 --yaw 0 --frame-id base_link --child-frame-id camera_link &

sleep 2

rviz2 -d /mnt/c/Users/jatin/soccer_bot/scripts/soccer_bot.rviz
