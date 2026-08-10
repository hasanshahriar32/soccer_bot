#!/usr/bin/env python3
"""
====================================================================
           SOCCER BOT - WINDOWS & WSL MASTER LAUNCHER
====================================================================
Description:
    Master orchestration script for Windows 10/11 environments.
    - Connects to Raspberry Pi over SSH to launch Lidar (5000) & Camera (8080).
    - Checks and launches VcXsrv X-Server for Windows X11 forwarding.
    - Starts WSL ROS 2 sensor hubs (Lidar, Camera, 3D Robot Model).
    - Opens RViz2 GUI with 3D viewport, 360 Lidar, and live camera feed.

Author: Antigravity AI
====================================================================
"""

import paramiko
import time
import subprocess
import os
import sys

# Raspberry Pi Network Credentials
PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

# Absolute Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RVIZ_CONFIG = "/mnt/c/Users/taufi/Desktop/soccer_bot/soccer_bot.rviz"

def log(msg, symbol="*"):
    print(f"[{symbol}] {msg}")

def launch_pi_sensors():
    log("Connecting to Raspberry Pi & initializing Lidar + Camera...", symbol="1/4")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
        
        # Kill lingering sensor processes
        ssh.exec_command("sudo killall -9 rpicam-vid python3 start_camera.sh ; docker stop soccer_bot_edge")
        time.sleep(1.0)
        
        # Launch Lidar TCP (port 5000) and Camera HTTP (port 8080)
        ssh.exec_command("nohup python3 ~/python_socat.py > ~/socat.log 2>&1 &")
        ssh.exec_command("nohup python3 ~/picam_server.py > ~/camera.log 2>&1 &")
        time.sleep(2.0)
        
        s, o, e = ssh.exec_command("ps aux | grep -E 'python_socat|picam_server'")
        log("Pi Hardware Status:\n" + o.read().decode().strip(), symbol="OK")
        ssh.close()
    except Exception as err:
        log(f"Warning: Failed to connect to Pi ({err}). Continuing local launch...", symbol="!")

def check_vcxsrv():
    log("Checking Windows VcXsrv X-Server...", symbol="2/4")
    try:
        tasklist = subprocess.check_output("tasklist", shell=True).decode()
        if "vcxsrv.exe" not in tasklist.lower():
            log("Starting VcXsrv X-Server with OpenGL support...", symbol="+")
            possible_paths = [
                r"C:\Program Files\VcXsrv\vcxsrv.exe",
                r"C:\Program Files (x86)\VcXsrv\vcxsrv.exe",
                r"C:\Users\taufi\Desktop\vcxsrv.exe"
            ]
            exe_path = next((p for p in possible_paths if os.path.exists(p)), None)
            if exe_path:
                subprocess.Popen([exe_path, ":0", "-ac", "-multiwindow", "-clipboard", "-wgl"])
                time.sleep(2.0)
            else:
                log("VcXsrv executable not found in default paths. Ensure VcXsrv is running.", symbol="!")
        else:
            log("VcXsrv X-Server is already running.", symbol="OK")
    except Exception as e:
        log(f"VcXsrv check notice: {e}", symbol="!")

def launch_wsl_nodes():
    log("Launching ROS 2 Sensor Hubs & 3D Model in WSL...", symbol="3/4")
    
    # 1. Start Openbox Window Manager in WSL
    subprocess.Popen('wsl -d Ubuntu -- bash -c "export DISPLAY=$(ip route show default | awk \'{print $3}\'):0 && openbox &"', shell=True)
    time.sleep(1.0)
    
    # 2. Launch Raw Lidar Publisher (/scan)
    lidar_cmd = 'wsl -d Ubuntu -- bash -c "source /opt/ros/jazzy/setup.bash && python3 /mnt/c/Users/taufi/Desktop/soccer_bot/raw_lidar_publisher.py"'
    subprocess.Popen(lidar_cmd, shell=True)
    
    # 3. Launch Camera Hub Node (/image_raw)
    camera_cmd = 'wsl -d Ubuntu -- bash -c "source /opt/ros/jazzy/setup.bash && python3 /mnt/c/Users/taufi/Desktop/soccer_bot/src/soccer_vision/soccer_vision/camera_hub_node.py"'
    subprocess.Popen(camera_cmd, shell=True)
    
    # 4. Launch 3D Robot Model Publisher (/robot_description)
    model_cmd = 'wsl -d Ubuntu -- bash -c "source /opt/ros/jazzy/setup.bash && python3 /mnt/c/Users/taufi/Desktop/soccer_bot/robot_model_publisher.py"'
    subprocess.Popen(model_cmd, shell=True)
    
    time.sleep(2.0)

def launch_rviz_gui():
    log("Opening RViz2 GUI on Windows Desktop...", symbol="4/4")
    rviz_cmd = (
        'wsl -d Ubuntu -- bash -c "'
        'export DISPLAY=$(ip route show default | awk \'{print $3}\'):0 && '
        'export QT_QPA_PLATFORM=xcb && '
        'export LIBGL_ALWAYS_SOFTWARE=1 && '
        'source /opt/ros/jazzy/setup.bash && '
        f'rviz2 -d {RVIZ_CONFIG}"'
    )
    subprocess.Popen(rviz_cmd, shell=True)

def main():
    print("=" * 60)
    print("      SOCCER BOT - WINDOWS & WSL ROBOTICS LAUNCHER      ")
    print("=" * 60)
    
    launch_pi_sensors()
    check_vcxsrv()
    launch_wsl_nodes()
    launch_rviz_gui()
    
    print("\n" + "=" * 60)
    log("SOCCER BOT LAUNCH COMPLETE!", symbol="SUCCESS")
    log(f"Camera Web Feed available at: http://{PI_IP}:8080/video", symbol="CAM")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()
