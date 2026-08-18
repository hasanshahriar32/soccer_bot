#!/bin/bash
# ============================================================
# Soccer Bot RViz2 Master Launcher for WSL2 + VcXsrv
# ============================================================

# Clean exit handler
cleanup() {
    pkill -P $$ 2>/dev/null || true
    pkill -9 -f lidar_hub_node 2>/dev/null || true
    pkill -9 -f camera_hub_node 2>/dev/null || true
    pkill -9 -f raw_lidar_publisher 2>/dev/null || true
    pkill -9 -f robot_model_publisher 2>/dev/null || true
    pkill -9 -f path_publisher 2>/dev/null || true
    pkill -9 -f rviz2 2>/dev/null || true
    exit 0
}
trap cleanup EXIT INT TERM

# 1. Clean up old background processes
pkill -9 -f lidar_hub_node 2>/dev/null || true
pkill -9 -f camera_hub_node 2>/dev/null || true
pkill -9 -f raw_lidar_publisher 2>/dev/null || true
pkill -9 -f robot_model_publisher 2>/dev/null || true
pkill -9 -f path_publisher 2>/dev/null || true
pkill -9 -f rviz2 2>/dev/null || true

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

# Workspace base path
WSL_BASE="/mnt/c/Users/taufi/Desktop/soccer_bot"

echo "==========================================================="
echo "   Launching RViz2 GUI on DISPLAY: $DISPLAY"
echo "==========================================================="

# 4. Start ROS 2 Sensor & Model Hub Nodes
python3 "${WSL_BASE}/scripts/raw_lidar_publisher.py" &
python3 "${WSL_BASE}/src/soccer_vision/soccer_vision/camera_hub_node.py" &
python3 "${WSL_BASE}/scripts/robot_model_publisher.py" &

sleep 2

# 5. Launch RViz2 GUI
RVIZ_CFG="${WSL_BASE}/soccer_bot.rviz"
if [ ! -f "$RVIZ_CFG" ]; then
    RVIZ_CFG="${WSL_BASE}/scripts/soccer_bot.rviz"
fi

echo "Opening RViz2 viewport using config: $RVIZ_CFG"
rviz2 -d "$RVIZ_CFG"
