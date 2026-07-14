FROM ros:jazzy-ros-base

RUN apt-get update && apt-get install -y \
    ros-jazzy-v4l2-camera \
    git cmake build-essential \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# Copy the local patched src workspace
COPY src /ros2_ws/src

# Build YDLidar SDK
WORKDIR /ros2_ws/src/YDLidar-SDK/build
RUN cmake .. && make && make install

# Build ROS workspace
WORKDIR /ros2_ws
RUN . /opt/ros/jazzy/setup.sh && colcon build

COPY scripts/soccer_bot_docker/entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
