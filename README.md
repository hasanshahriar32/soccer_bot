# Autonomous ROS 2 Soccer Robot

This project implements a fully autonomous soccer-playing robot using ROS 2 Jazzy. The system is built on a distributed architecture utilizing a Raspberry Pi 3B as an Edge Node for hardware interfaces, and a Laptop as a central processing hub for Computer Vision and navigation logic.

## 🏗️ Architecture Overview

To maximize performance on the Raspberry Pi 3B (which is resource-constrained) and avoid complex driver permission issues, the architecture is split into two halves:

1. **Raspberry Pi (Edge Node):** 
   - Handles the physical hardware. 
   - Runs a highly optimized `soccer_bot_edge` Docker container in `--net=host` mode to natively interface with the YDLidar over USB and broadcast `/scan` data across the network via ROS 2 DDS.
   - Runs a lightweight background script (`start_camera.sh`) using the native `rpicam-vid` application to host a highly resilient, low-latency raw MJPEG stream of the CSI camera.
2. **Laptop (Compute Hub):**
   - Runs heavy Computer Vision tasks (OpenCV ball detection), path planning, and RViz visualization.
   - Runs a custom python TCP server (`camera_hub_node.py`) that constantly listens for the Pi's camera stream. If the connection drops, it automatically handles reconnects.
   - Processes the raw Lidar `/scan` and camera `/image_raw` topics to make driving decisions.

## 🚀 How to Run the System

The entire startup process is fully automated via SSH from the laptop. You do not need to manually run commands on the Pi.

1. Turn on the Raspberry Pi and ensure both the Pi and Laptop are on the same Wi-Fi network.
2. On the laptop, open a terminal in the `soccer_bot` workspace.
3. Run the orchestration script:
   ```bash
   bash scripts/start_laptop_hub.sh
   ```
   
**What this script does automatically:**
- SSHes into the Pi and kills any old rogue camera processes.
- Starts the `start_camera.sh` daemon on the Pi to stream the camera feed.
- Starts the `camera_hub_node` on the laptop to decode the TCP camera stream into ROS 2 `Image` messages.
- (The Lidar stream is handled entirely automatically in the background via the Pi's Docker container, which starts automatically on boot).

### Visualizing the Data

Once the hub script is running, open a **NEW terminal** on the laptop and launch RViz2:
```bash
source /opt/ros/jazzy/setup.bash
rviz2
```
- **To view Lidar:** Add a `LaserScan` display and subscribe to the `/scan` topic. Set the Fixed Frame to `laser_frame`.
- **To view Camera:** Add an `Image` display and subscribe to the `/image_raw` topic.

## 🛠️ Sensor Details & Troubleshooting

### YDLidar X4
- **Interface:** Natively published from the Pi via ROS 2 DDS.
- **Driver:** The `ydlidar_ros2_driver` runs inside the Pi's `soccer_bot_edge` container. The container runs with `--net=host` to ensure seamless discovery by the laptop. 
- **Troubleshooting:** If the Lidar isn't showing up, ensure the Pi and Laptop are on the same Wi-Fi, and that the Pi's docker container is running (`docker ps`).

### Raspberry Pi Camera Module V2 (CSI)
- **Interface:** Raw MJPEG over TCP port 8000.
- **Why TCP and not ROS 2 DDS?** Pushing 15 FPS video through ROS 2 serialization natively on a Pi 3B consumes 100% CPU. Bypassing ROS on the Pi and using a raw TCP stream directly into the laptop (where it's then converted to a ROS 2 topic) results in 0 latency and extremely low Pi CPU usage.
- **Resiliency:** The Pi actively tries to connect to the laptop. If you restart the laptop hub, the Pi will automatically reconnect within 2 seconds.

## 🔮 Next Steps: Sensor Fusion

In the future, we will combine the spatial data (Lidar) with the visual data (Camera) to accurately detect the distance of objects seen in the frame.
This will be achieved by defining a **Static TF2 Transform** that maps the physical real-world distance between the camera lens and the lidar laser plane. Once published, ROS 2's `message_filters` will sync the timestamps, allowing RViz to dynamically overlay the laser dots directly onto the live camera image.
