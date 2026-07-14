# Physical Deployment Guide

This guide outlines the exact steps to transition your autonomous soccer bot from laptop development to the physical Raspberry Pi hardware.

## Phase 1: OS Installation
1. Download the **Raspberry Pi Imager** tool from the official website.
2. Insert a microSD card (at least 32GB recommended) into your computer.
3. In the Imager:
   - **Choose OS**: Select `Other general-purpose OS` -> `Ubuntu` -> `Ubuntu Server 24.04 LTS (64-bit)`.
   - **Choose Storage**: Select your microSD card.
   - **Advanced Options (Gear Icon)**:
     - Set hostname to `soccerbot`.
     - Enable SSH (Use password authentication).
     - Set username and password.
     - Configure wireless LAN (Enter your Wi-Fi details so it connects automatically).
4. Click **Write** and wait for it to finish.

## Phase 2: Hardware Assembly
1. Insert the microSD card into the Raspberry Pi.
2. Connect the **Raspberry Pi Camera** to the CSI port using the ribbon cable.
3. Plug the **YDLidar** into one of the USB 3.0 (blue) ports.
4. Wire your **Motor Driver (e.g., L298N)** to the GPIO pins of the Raspberry Pi. *(See README.md for pin configurations, or map them as needed in the code).*
5. Connect power to the Pi (via USB-C or GPIO) and power it on.

## Phase 3: Transferring the Workspace
Since you enabled SSH during OS flashing, you can transfer the files wirelessly from your laptop to the Pi.
Open a terminal on your laptop and run:
```bash
# Compress the workspace
tar -czvf soccer_bot.tar.gz -C /home/sharmin/Desktop/iot soccer_bot/

# Send it to the Raspberry Pi (replace <username> and <pi_ip_address>)
scp soccer_bot.tar.gz <username>@<pi_ip_address>:~/

# SSH into the Pi
ssh <username>@<pi_ip_address>

# On the Pi, extract the workspace
tar -xzvf soccer_bot.tar.gz
```

## Phase 4: Running the Setup
Now that you are SSH'd into the Raspberry Pi and the folder is there, run the automated setup script:
```bash
cd ~/soccer_bot
chmod +x scripts/setup_pi.sh
./scripts/setup_pi.sh
```
*Note: This script will take a while as it downloads ROS 2 and OpenCV.*

## Phase 5: Building and Testing
Once the setup script finishes:
1. **Compile**:
   ```bash
   cd ~/soccer_bot
   colcon build
   source install/setup.bash
   ```
2. **Test Vision**: 
   ```bash
   ros2 run soccer_vision ball_tracker
   ```
3. **Test Lidar**:
   ```bash
   ros2 run soccer_navigation obstacle_avoidance
   ```
