#!/bin/bash
# ============================================================
# Soccer Bot RViz2 Master Launcher for WSL2 + VcXsrv
# ============================================================

# Auto-detect Workspace base path across environments
if [ -d "/mnt/c/Users/jatin/soccer_bot" ]; then
    WSL_BASE="/mnt/c/Users/jatin/soccer_bot"
elif [ -d "/mnt/c/Users/taufi/Desktop/soccer_bot" ]; then
    WSL_BASE="/mnt/c/Users/taufi/Desktop/soccer_bot"
else
    WSL_BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
fi

# Clean exit handler
cleanup() {
    pkill -P $$ 2>/dev/null || true
    pkill -9 -f lidar_hub_node 2>/dev/null || true
    pkill -9 -f camera_hub_node 2>/dev/null || true
    pkill -9 -f ball_tracker_node 2>/dev/null || true
    pkill -9 -f raw_lidar_publisher 2>/dev/null || true
    pkill -9 -f robot_model_publisher 2>/dev/null || true
    pkill -9 -f fast_occupancy_mapper 2>/dev/null || true
    pkill -9 -f pi_screen_streamer 2>/dev/null || true
    pkill -9 -f path_publisher 2>/dev/null || true
    pkill -9 -f rviz2 2>/dev/null || true
    exit 0
}
trap cleanup EXIT INT TERM

# 1. Clean up old background processes
cleanup 2>/dev/null || true

# 2. X11 Display & Glibc Priority Fixes for WSL2
HOST_IP=$(ip route show default | awk '{print $3}')
export DISPLAY="${HOST_IP}:0"
export QT_QPA_PLATFORM=xcb
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
export OMP_NUM_THREADS=1
export RMW_FASTRTPS_USE_QOS_FROM_XML=0

# 3. Source ROS 2 (Jazzy / Humble)
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
elif [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
fi

echo "==========================================================="
echo "   Launching RViz2 GUI on DISPLAY: $DISPLAY"
echo "   Workspace: $WSL_BASE"
echo "==========================================================="

# 4. Start ROS 2 Sensor, Model, Mapping & Vision Tracking Nodes
python3 "${WSL_BASE}/scripts/raw_lidar_publisher.py" &
python3 "${WSL_BASE}/src/soccer_vision/soccer_vision/camera_hub_node.py" 2>/dev/null &
python3 "${WSL_BASE}/src/soccer_vision/soccer_vision/ball_tracker_node.py" 2>/dev/null &
python3 "${WSL_BASE}/scripts/robot_model_publisher.py" &
python3 "${WSL_BASE}/scripts/path_publisher.py" 2>/dev/null &
python3 "${WSL_BASE}/scripts/fast_occupancy_mapper.py" &
python3 "${WSL_BASE}/src/soccer_slam/soccer_slam/pi_screen_streamer.py" 2>/dev/null &

sleep 2

# 5. Launch RViz2 GUI
RVIZ_CFG="${WSL_BASE}/soccer_bot.rviz"
if [ ! -f "$RVIZ_CFG" ]; then
    RVIZ_CFG="${WSL_BASE}/scripts/soccer_bot.rviz"
fi

echo "Opening RViz2 viewport using config: $RVIZ_CFG"
rviz2 -d "$RVIZ_CFG"
