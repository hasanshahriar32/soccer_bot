# 🤖 Soccer Bot - Master System Guide & Saved Configuration

This repository contains the complete robotics stack for the Autonomous Soccer Bot, pre-configured for automated 1-click startup on Windows and WSL.

---

## ⚡ 1-Click Startup

### Double-Click from your Desktop:
```text
C:\Users\jatin\Desktop\START_SOCCER_BOT.bat
```
*(Or in the repository: `C:\Users\jatin\soccer_bot\windows\START_SOCCER_BOT.bat`)*

**What this automatically executes in 1 click:**
1. Starts the **VcXsrv X-Server** on Windows silently (`:0`).
2. Connects to the **Raspberry Pi (`192.168.0.135`)** and starts the 360° LIDAR bridge (Port 5000) and high-speed Camera server (Port 8000).
3. Launches **ROS 2 Humble** sensor hubs in WSL (`/scan`, `/image_raw`, `robot_state_publisher`, `TF`).
4. Opens **RViz2 3D Interface** and the **Live Sensor Dashboard**.

---

## 🏎️ Motor Control Commands

### 1. Interactive Keyboard Remote Control (Teleop):
```powershell
cd C:\Users\jatin\soccer_bot
python motor_control/teleop_keyboard.py
```
- <kbd>W</kbd>: Move Forward
- <kbd>S</kbd>: Move Backward
- <kbd>A</kbd>: Turn Left
- <kbd>D</kbd>: Turn Right
- <kbd>Space</kbd> / <kbd>X</kbd>: Stop
- <kbd>Q</kbd>: Quit

### 2. Continuous Spinning:
```powershell
python motor_control/spin_continuous.py --dir F    # Forward
python motor_control/spin_continuous.py --dir L    # Left Rotation (CCW)
python motor_control/spin_continuous.py --dir R    # Right Rotation (CW)
```

---

## 📌 Hardware Pinout & Network Map

| Component | Port / Pin | Protocol | Description |
| :--- | :--- | :--- | :--- |
| **Raspberry Pi** | `192.168.0.135:22` | SSH | User: `hasan` / Pass: `grammarpro` |
| **360° YDLIDAR** | Port `5000` (TCP) | `/scan` (`sensor_msgs/LaserScan`) | 360° range array |
| **CSI Camera** | Port `8000` (TCP) | `/image_raw` (`sensor_msgs/Image`) | Live 640x480 video at 25 FPS |
| **Arduino Uno** | `/dev/ttyACM0` | 9600 Baud (`F`, `B`, `L`, `R`, `S`) | L298N Motor Driver |
| **Left Motor** | `ENA=5`, `IN1=9`, `IN2=10` | PWM Speed & Direction | Left Drive Wheels |
| **Right Motor** | `ENB=6`, `IN3=11`, `IN4=12` | PWM Speed & Direction | Right Drive Wheels |
