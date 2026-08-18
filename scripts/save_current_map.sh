#!/bin/bash
# ====================================================================
# Soccer Bot Map Snapshot & Save Utility
# ====================================================================

MAP_NAME="${1:-soccer_bot_room_map_$(date +%Y%m%d_%H%M%S)}"

echo "=================================================="
echo " 💾 Saving Current SLAM Map: $MAP_NAME"
echo "=================================================="

source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

# Run map saver node
ros2 run soccer_slam slam_map_saver "$MAP_NAME"

echo "=================================================="
echo " Map files saved to: /home/sharmin/Desktop/iot/soccer_bot/src/soccer_slam/maps/"
echo "=================================================="
