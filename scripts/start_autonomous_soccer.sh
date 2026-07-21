#!/bin/bash
# start_autonomous_soccer.sh
# Master launcher for Autonomous Soccer Bot Ball Seeking & Autonomous Drive

source /opt/ros/jazzy/setup.bash
source /home/sharmin/Desktop/iot/soccer_bot/install/setup.bash

echo "=========================================="
echo " Launching Autonomous Soccer Bot System..."
echo "=========================================="

# 1. Kill existing brain / vision nodes if running
pkill -f ball_tracker_node 2>/dev/null
pkill -f soccer_brain_node 2>/dev/null

# 2. Launch Ball Tracker Vision Node (Camera -> /ball_position)
echo "Launching Vision Ball Tracker Node..."
python3 /home/sharmin/Desktop/iot/soccer_bot/src/soccer_vision/soccer_vision/ball_tracker_node.py &
sleep 1

# 3. Launch Autonomous Core Brain Node (/ball_position + /scan -> /cmd_vel)
echo "Launching Autonomous Core Brain Decision Engine..."
python3 /home/sharmin/Desktop/iot/soccer_bot/src/core_brain/soccer_brain_node.py &

echo ""
echo "Autonomous Soccer Bot is LIVE and seeking the ball!"
echo "Press Ctrl+C to stop."
echo ""

wait
