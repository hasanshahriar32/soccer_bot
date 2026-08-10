# 🪟 Windows Setup & Deployment Guide for Soccer Bot

This guide provides step-by-step instructions for installing, configuring, and running the **ROS 2 Jazzy Soccer Bot System** on a **Windows 10 / Windows 11 PC** using **WSL2 (Ubuntu 24.04 LTS)** and **VcXsrv X-Server**.

---

## 📋 System Prerequisites

| Component | Required Version / Setting |
| :--- | :--- |
| **OS** | Windows 10 (Build 19041+) or Windows 11 |
| **WSL** | WSL2 with Ubuntu 24.04 LTS |
| **ROS 2** | ROS 2 Jazzy Jalisco (`ros-jazzy-desktop`) |
| **X-Server** | VcXsrv Windows X-Server |
| **Python** | Python 3.10+ on Windows & WSL |

---

## 🛠️ Step 1: Install WSL2 & Ubuntu 24.04 LTS

1. Open PowerShell as **Administrator** on Windows and run:
   ```cmd
   wsl --install -d Ubuntu
   ```
2. Reboot your computer if prompted.
3. Open the **Ubuntu** app from your Windows Start Menu and set up your Linux username and password.

---

## 🛠️ Step 2: Install ROS 2 Jazzy & Dependencies inside WSL2

Open your **Ubuntu terminal** inside WSL and run the following setup commands:

```bash
# Update System
sudo apt update && sudo apt upgrade -y

# Add ROS 2 Jazzy Repository
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install ROS 2 Jazzy Desktop & Tools
sudo apt update
sudo apt install -y ros-jazzy-desktop \
                    python3-colcon-common-extensions \
                    ros-jazzy-cv-bridge \
                    python3-opencv \
                    python3-serial \
                    openbox \
                    x11-apps

# Auto-Source ROS 2 in bashrc
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## 🛠️ Step 3: Install VcXsrv X-Server on Windows

1. Download and run the **VcXsrv Windows X-Server Installer** (`vcxsrv-64.1.20.14.0.installer.exe`).
2. Complete the installation wizard using default settings.
3. When starting VcXsrv for the first time, use these exact settings:
   - **Display settings**: `Multiple windows` (Display number: `0`)
   - **Client startup**: `Start no client`
   - **Extra settings**:
     - ✅ Check `Clipboard`
     - ✅ Check `Disable access control` (`-ac`)
     - ✅ Check `Native OpenGL` (`-wgl`)
4. Save the configuration to your Desktop as `config.xlaunch` for easy 1-click startup.

---

## 🚀 Step 4: Running the System on Windows (1-Click Startup)

To run the entire system (Raspberry Pi Lidar, Pi Camera, WSL ROS 2 hubs, and RViz GUI):

### Method 1: 1-Click Desktop Batch Shortcut
Double-click **`windows/START_SOCCER_BOT.bat`** (or the **`START_SOCCER_BOT.bat`** shortcut on your Desktop).

### Method 2: Manual PowerShell Command
Open Command Prompt or PowerShell and run:
```cmd
python C:\Users\taufi\Desktop\soccer_bot\windows\launch_windows_hub.py
```

---

## 🔍 Troubleshooting & Verification

### 1. RViz Displaying Blank / Black Window
If RViz opens as a blank black window, set environment variables inside WSL:
```bash
export DISPLAY=$(ip route show default | awk '{print $3}'):0
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
rviz2 -d /mnt/c/Users/taufi/Desktop/soccer_bot/soccer_bot.rviz
```

### 2. Camera Stream Verification
Open your browser on Windows and navigate to:
👉 **`http://192.168.0.135:8080/video`**

### 3. Topic Verification inside WSL
```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list
# You should see:
#   /scan
#   /image_raw
#   /robot_description
#   /tf
#   /tf_static
```
