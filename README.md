# ⚽ Autonomous ROS 2 Soccer Robot

An autonomous soccer-playing robotics system built on **ROS 2 Jazzy Jalisco**. 
The system features a distributed architecture across a **Raspberry Pi 3B (Edge Node)** for sensor streaming & motor driving, and a **Laptop (Compute Hub)** running on **Windows 11 / WSL2** or **Linux** for Computer Vision, Navigation, and RViz 3D Visualization.

---

## 📁 Repository Directory Structure

```text
soccer_bot/
├── docs/                             # Documentation Guides
│   ├── WINDOWS_SETUP_GUIDE.md        # Detailed Windows 11 + WSL2 + VcXsrv Setup Guide
│   ├── PHYSICAL_DEPLOYMENT_GUIDE.md  # Raspberry Pi OS Flashing & Hardware Wiring Guide
│   └── NOTES.md                      # System Architecture & Development Notes
├── windows/                          # Windows Specific Launchers & Configuration
│   ├── START_SOCCER_BOT.bat          # 1-Click Desktop Batch Launcher for Windows
│   └── launch_windows_hub.py         # Master Python Orchestrator for Windows + WSL + Pi
├── scripts/                          # ROS 2 Python Nodes & URDF Models
│   ├── robot.urdf                    # Official 3D URDF Description (Chassis, Wheels, Sensors)
│   ├── raw_lidar_publisher.py        # Raw TCP Lidar Packet Parser Node (/scan)
│   ├── robot_model_publisher.py      # ROS 2 robot_description & Static TF Publisher Node
│   └── start_laptop_hub.sh           # Linux Bash Startup Orchestrator
├── src/                              # ROS 2 Packages Workspace
│   ├── soccer_vision/                # Camera Receiver Node & HSV Color Tracking
│   ├── soccer_navigation/            # Reactive Obstacle Avoidance & Path Planning
│   └── rosboard/                     # Optional Web-based ROS Dashboard
└── soccer_bot.rviz                   # Pre-configured RViz2 3D Viewport Profile
```

---

## 🪟 Windows Setup & 1-Click Execution (Recommended for Windows)

### 1-Click Startup:
Double-click **`windows/START_SOCCER_BOT.bat`** (or the **`START_SOCCER_BOT.bat`** shortcut on your Windows Desktop).

### What the 1-Click Launcher Does:
1. **Raspberry Pi SSH Connection:** Automatically starts the Lidar (`port 5000`) and Camera (`port 8080`) daemons on the Pi.
2. **VcXsrv X-Server Check:** Starts VcXsrv with OpenGL hardware acceleration.
3. **WSL2 ROS 2 Hubs:** Starts background nodes (`raw_lidar_publisher.py`, `camera_hub_node.py`, `robot_model_publisher.py`).
4. **RViz2 GUI:** Automatically opens the RViz 3D Viewport displaying the 3D Robot Model, 360° Lidar Radar, and Live Camera Feed.

> 📖 *For detailed step-by-step installation instructions for WSL2, VcXsrv, and ROS 2 Jazzy on Windows, see [`docs/WINDOWS_SETUP_GUIDE.md`](docs/WINDOWS_SETUP_GUIDE.md).*

---

## 🐧 Linux Setup & Execution

### 1. Build the Workspace:
```bash
cd soccer_bot
colcon build
source install/setup.bash
```

### 2. Launch the System Hub:
```bash
bash scripts/start_laptop_hub.sh
```

### 3. Launch RViz2 Visualization:
```bash
source /opt/ros/jazzy/setup.bash
rviz2 -d soccer_bot.rviz
```

---

## 📐 Robot Model & Physical Dimensions

- **Chassis Body:** `0.33 m` (L) x `0.17 m` (W) x `0.11 m` (H) Rectangular Blue Box
- **Drive Wheels:** 2 Rear Drive Wheels (`radius: 3.3 cm`, `length: 4.0 cm`) positioned at `xyz="-0.115 ±0.105 0.033"`
- **YDLidar X4:** Top-mounted Red Laser Sensor (`radius: 3.5 cm`, `length: 4.0 cm`) positioned at `laser_frame`
- **Pi Camera V2:** Front Green CSI Camera Module (`1.0cm x 3.0cm x 3.0cm`) positioned at `camera_link`

---

## 🌐 Live Camera Web Stream

When the system is active, you can also view the live camera feed in any browser:
👉 **`http://192.168.0.135:8080/video`**
