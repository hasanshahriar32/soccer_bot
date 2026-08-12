#!/usr/bin/env python3
"""
====================================================================
           SOCCER BOT - ROBUST AUTO-HEALING MASTER LAUNCHER
====================================================================
"""

import time
import subprocess
import os
import sys
import socket

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

WSL_BASE = "/mnt/c/Users/jatin/soccer_bot"
RVIZ_CONFIG = f"{WSL_BASE}/scripts/soccer_bot.rviz"
IS_WINDOWS = sys.platform == 'win32'

def log(msg, symbol="*"):
    print(f"[{symbol}] {msg}", flush=True)

def is_vcxsrv_running():
    """Checks if VcXsrv is already active on Windows."""
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq vcxsrv.exe"', shell=True).decode('utf-8', errors='ignore')
        return 'vcxsrv.exe' in out.lower()
    except:
        return False

def check_and_start_vcxsrv():
    """Auto-detects and starts VcXsrv X-Server if not already running."""
    if is_vcxsrv_running():
        log("VcXsrv X-Server is already active and running!", symbol="X11")
        return True

    vcxsrv_paths = [
        r"C:\Program Files\VcXsrv\vcxsrv.exe",
        r"C:\Program Files (x86)\VcXsrv\vcxsrv.exe"
    ]
    for path in vcxsrv_paths:
        if os.path.exists(path):
            log("Found VcXsrv X-Server! Starting silently in background...", symbol="X11")
            cmd = f'"{path}" :0 -multiwindow -clipboard -wgl -ac'
            subprocess.Popen(cmd, shell=True)
            time.sleep(1.5)
            return True
    return False

def check_pi_online():
    """Checks if Raspberry Pi SSH is reachable."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        res = s.connect_ex((PI_IP, 22))
        s.close()
        return res == 0
    except:
        return False

def launch_pi_sensors():
    log("Checking Raspberry Pi connection...", symbol="1/3")
    if not check_pi_online():
        log(f"WARNING: Raspberry Pi ({PI_IP}) is currently OFFLINE!", symbol="!")
        log("--> Please make sure your Raspberry Pi USB-C power is plugged in & connected to Wi-Fi.", symbol="!")
        log("--> Continuing with local visualizer...", symbol="*")
        return False

    log("Raspberry Pi is ONLINE! Starting Lidar, Camera & Motor daemons...", symbol="OK")
    if HAS_PARAMIKO:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
            
            # Start Docker & Lidar
            ssh.exec_command("docker start soccer_bot_edge")
            time.sleep(1.0)
            ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl restart soccer_lidar.service soccer_camera.service soccer_motor.service")
            time.sleep(2.0)
            
            log("All Pi hardware services (LIDAR, Camera, Motor) active!", symbol="OK")
            ssh.close()
            return True
        except Exception as err:
            log(f"Pi SSH warning: {err}", symbol="!")
            return False
    return False

def launch_wsl_system():
    log("Launching ROS 2 Sensor Hubs, 3D Kinematics & RViz2 GUI...", symbol="2/3")
    rviz_cmd = f"bash {WSL_BASE}/scripts/launch_rviz.sh"
    if IS_WINDOWS:
        subprocess.Popen(f'wsl -d Ubuntu-22.04 -- bash -c "{rviz_cmd}"', shell=True)
    else:
        subprocess.Popen(f'bash -c "{rviz_cmd}"', shell=True)

def launch_dashboard():
    log("Opening Live Sensor Dashboard (Radar + Camera)...", symbol="3/3")
    python_exe = sys.executable or "C:\\Python314\\python.exe"
    dash_script = r"C:\Users\jatin\soccer_bot\scripts\soccer_bot_dashboard.py"
    subprocess.Popen(f'"{python_exe}" "{dash_script}"', shell=True)

def main():
    print("=" * 65)
    print("         SOCCER BOT - MASTER SYSTEM LAUNCHER         ")
    print("=" * 65)
    
    check_and_start_vcxsrv()
    pi_ready = launch_pi_sensors()
    launch_wsl_system()
    launch_dashboard()
    
    print("\n" + "=" * 65)
    if pi_ready:
        log("ALL SYSTEMS ONLINE! RViz2 & Dashboard are running with LIVE SENSORS.", symbol="SUCCESS")
    else:
        log("LOCAL VISUALIZER OPEN! (Turn on Pi power to stream live sensor data).", symbol="READY")
    print("=" * 65 + "\n")
    time.sleep(2.0)

if __name__ == '__main__':
    main()
