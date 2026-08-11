# 🏎️ Soccer Bot - Motor Control Subsystem

This folder contains all firmware, serial drivers, ROS 2 bridges, and keyboard teleoperation tools for controlling the robot's dual DC drive motors.

---

## 📌 Hardware Pinout & Wiring

- **Board:** Arduino Uno R3 connected via USB to Raspberry Pi (`/dev/ttyACM0`)
- **Driver:** L298N Dual H-Bridge Motor Driver
- **Serial Configuration:** `9600 Baud`, `8N1`

| Motor Channel | L298N Pin | Arduino Uno Pin | Function |
| :--- | :--- | :--- | :--- |
| **Left Motor** | **`ENA`** | **Pin 5** (PWM) | Left Speed (0 - 255) |
| | **`IN1`** | **Pin 9** | Left Direction A |
| | **`IN2`** | **Pin 10** | Left Direction B |
| **Right Motor** | **`ENB`** | **Pin 6** (PWM) | Right Speed (0 - 255) |
| | **`IN3`** | **Pin 11** | Right Direction A |
| | **`IN4`** | **Pin 12** | Right Direction B |

---

## 🕹️ Serial Command Protocol

Send single ASCII characters over serial:

| Command | Action | Left Motor | Right Motor |
| :---: | :--- | :---: | :---: |
| **`'F'`** | **Forward** | Forward | Forward |
| **`'B'`** | **Backward** | Reverse | Reverse |
| **`'L'`** | **Turn Left** | Reverse | Forward |
| **`'R'`** | **Turn Right** | Forward | Reverse |
| **`'S'`** | **Stop** | Coast/Brake (PWM 0) | Coast/Brake (PWM 0) |

---

## 🚀 Quick Usage Commands

### 1. Interactive Keyboard Remote Control (Teleop)
Drive the robot using your laptop keyboard in real time:
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

---

### 2. Automated Motor Diagnostic Test
Run a full test sequence (Forward -> Stop -> Backward -> Stop -> Left -> Right):
```powershell
cd C:\Users\jatin\soccer_bot
python motor_control/test_motors.py
```

---

### 3. ROS 2 `/cmd_vel` Motor Bridge
Run the ROS 2 node to translate navigation velocity topics into motor movements:
```bash
wsl bash -c "source /opt/ros/humble/setup.bash && python3 /mnt/c/Users/jatin/soccer_bot/motor_control/motor_bridge_node.py"
```
