#!/usr/bin/env python3
"""
====================================================================
           SOCCER BOT - UNIFIED MASTER SYSTEM LAUNCHER
====================================================================
Launches ALL components with a single command / double-click:
  1. VcXsrv Windows X11 Server (:0)
  2. Raspberry Pi Hardware Daemons:
     - LiDAR Socket Bridge (Port 5000)
     - Camera Fast JPEG Streamer (Port 8000)
     - Motor Wheel Controller (Port 9000)
     - 4-DOF Robotic Arm Handling Server (Port 9001)
     - Physical Pi 480x320 LCD Screen Live SLAM Map HUD
  3. WSL2 (Ubuntu-22.04) ROS 2 Nodes:
     - LiDAR LaserScan Publisher
     - Camera Hub & Vision Tracker
     - 2D Fast Occupancy Grid SLAM Mapper (/map)
     - Pi Screen Map Streamer (Port 8765)
     - RViz2 3D Robot Visualizer Viewport
  4. Windows Native Motor & Arm Teleoperation Controller GUI
====================================================================
"""

import time
import subprocess
import os
import sys
import socket
import concurrent.futures
import webbrowser

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

DEFAULT_PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

drive = REPO_DIR[0].lower()
rest = REPO_DIR[2:].replace("\\", "/")
WSL_BASE = f"/mnt/{drive}{rest}"

IS_WINDOWS = sys.platform == 'win32'

def log(msg, symbol="*"):
    print(f"[{symbol}] {msg}", flush=True)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.168.0.1', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '192.168.0.116'
    finally:
        s.close()
    return ip

def get_wsl_distro():
    try:
        out = subprocess.check_output("wsl -l -q", shell=True).decode("utf-16", errors="ignore")
        for line in out.splitlines():
            line = line.strip()
            if "Ubuntu-22.04" in line:
                return "Ubuntu-22.04"
            if "Ubuntu" in line:
                return "Ubuntu"
    except Exception:
        pass
    return "Ubuntu-22.04"

def is_vcxsrv_running():
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq vcxsrv.exe"', shell=True).decode('utf-8', errors='ignore')
        return 'vcxsrv.exe' in out.lower()
    except Exception:
        return False

def check_and_start_vcxsrv():
    if is_vcxsrv_running():
        log("VcXsrv X-Server is already active!", symbol="X11")
        return True

    vcxsrv_paths = [
        r"C:\Program Files\VcXsrv\vcxsrv.exe",
        r"C:\Program Files (x86)\VcXsrv\vcxsrv.exe"
    ]
    for path in vcxsrv_paths:
        if os.path.exists(path):
            log("Starting VcXsrv X-Server in background...", symbol="X11")
            cmd = f'"{path}" :0 -multiwindow -clipboard -wgl -ac'
            subprocess.Popen(cmd, shell=True)
            time.sleep(1.5)
            return True
    return False

def test_ssh_ip(ip):
    try:
        s = socket.socket()
        s.settimeout(0.3)
        res = s.connect_ex((ip, 22))
        s.close()
        if res == 0:
            return ip
    except Exception:
        pass
    return None

def find_pi_ip():
    if test_ssh_ip(DEFAULT_PI_IP):
        return DEFAULT_PI_IP
        
    subnets = ['192.168.0', '10.61.32', '10.72.30', '10.127.69', '192.168.1', '192.168.43', '172.20.10']
    log("Scanning local networks for Raspberry Pi...", symbol="SEARCH")
    
    targets = [f"{sub}.{i}" for sub in subnets for i in range(1, 255)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
        results = ex.map(test_ssh_ip, targets)
        for ip in results:
            if ip and not ip.endswith('.1'):
                log(f"Auto-discovered Raspberry Pi at IP: {ip}", symbol="FOUND")
                return ip
    return None

def launch_pi_hardware(pi_ip):
    laptop_ip = get_local_ip()
    log(f"Connecting to Raspberry Pi at {pi_ip} (Laptop: {laptop_ip})...", symbol="1/4")
    if HAS_PARAMIKO:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(pi_ip, username=PI_USER, password=PI_PASS, timeout=8)
            
            # 1. Clean up old conflicting streaming processes
            ssh.exec_command(
                "echo grammarpro | sudo -S systemctl stop soccer_camera soccer_lidar soccer_motor 2>/dev/null ; "
                "echo grammarpro | sudo -S chmod 666 /dev/ttyACM* /dev/ttyUSB* 2>/dev/null ; "
                "pkill -9 -f rpicam 2>/dev/null ; "
                "pkill -9 -f fast_camera_server 2>/dev/null ; "
                "pkill -9 -f detect_live_picamera2 2>/dev/null ; "
                "pkill -9 -f python_socat 2>/dev/null ; "
                "pkill -9 -f lidar_bridge 2>/dev/null ; "
                "pkill -9 -f motor_server 2>/dev/null ; "
                "pkill -9 -f arm_server 2>/dev/null ; "
                "pkill -9 -f pi_screen_hud 2>/dev/null"
            )
            time.sleep(1.0)
            
            # 2. Launch LiDAR wireless bridge (Port 5000)
            ssh.exec_command("nohup python3 /home/hasan/lidar_bridge.py > ~/socat.log 2>&1 &")
            
            # 3. Launch Camera Fast JPEG stream (Port 8000)
            ssh.exec_command("nohup python3 /home/hasan/fast_camera_server.py > ~/cam.log 2>&1 &")
            
            # 4. Launch Motor Wheel Controller (Port 9000)
            ssh.exec_command("nohup python3 /home/hasan/motor_server.py > ~/motor.log 2>&1 &")
            
            # 5. Launch 4-DOF Robotic Arm Handling Server (Port 9001)
            ssh.exec_command("nohup python3 /home/hasan/arm_server.py > ~/arm.log 2>&1 &")
            
            # 6. Launch Raspberry Pi LCD Screen Live SLAM Navigation HUD
            ssh.exec_command(f"export DISPLAY=:0 ; export XAUTHORITY=/home/hasan/.Xauthority ; nohup python3 /home/hasan/pi_screen_hud.py {laptop_ip} > ~/hud.log 2>&1 &")
            
            time.sleep(1.5)
            log("Pi Hardware Initialized: LiDAR(5000), Camera(8000), Motors(9000), Arm(9001) & LCD Map HUD!", symbol="OK")
            ssh.close()
            return True
        except Exception as err:
            log(f"Pi SSH launch error: {err}", symbol="!")
            return False
    return False

def launch_wsl_system():
    distro = get_wsl_distro()
    log(f"Launching ROS 2 Sensor Hubs, Occupancy SLAM Mapper & RViz2 in WSL ({distro})...", symbol="2/4")
    
    rviz_cmd = f"bash {WSL_BASE}/scripts/launch_rviz.sh"
    if IS_WINDOWS:
        subprocess.Popen(f'wsl -d {distro} -- bash -c "{rviz_cmd}"', shell=True)
    else:
        subprocess.Popen(f'bash -c "{rviz_cmd}"', shell=True)

def launch_motor_controller():
    log("Opening Desktop Motor & Robotic Arm Controller GUI...", symbol="3/5")
    gui_script = os.path.join(REPO_DIR, "motor_control", "gui_teleop.py")
    py_exe = sys.executable
    try:
        subprocess.Popen([py_exe, gui_script], cwd=REPO_DIR)
    except Exception as e:
        log(f"Could not open GUI: {e}", symbol="!")

def launch_web_teleop(pi_ip):
    log("Starting Live Web Teleop & Camera Controller (Port 5050)...", symbol="4/5")
    web_script = os.path.join(REPO_DIR, "motor_control", "web_teleop_server.py")
    py_exe = sys.executable
    try:
        subprocess.Popen([py_exe, web_script, pi_ip or DEFAULT_PI_IP], cwd=REPO_DIR)
        time.sleep(1.5)
        local_ip = get_local_ip()
        log(f"Web Controller Ready! Open http://localhost:5050 or http://{local_ip}:5050", symbol="BROWSER")
        webbrowser.open("http://localhost:5050")
    except Exception as e:
        log(f"Could not open Web Teleop: {e}", symbol="!")

def main():
    print("=" * 68)
    print("        ⚽ SOCCER BOT - UNIFIED FULL SYSTEM MASTER LAUNCHER       ")
    print("=" * 68)
    
    check_and_start_vcxsrv()
    
    custom_ip = sys.argv[1] if len(sys.argv) > 1 else None
    pi_ip = custom_ip or find_pi_ip()
    
    pi_ready = False
    if pi_ip:
        pi_ready = launch_pi_hardware(pi_ip)
    else:
        log("Raspberry Pi (192.168.0.135) is currently unreachable.", symbol="!")
        log("--> Ensure Pi is powered ON with 5V/3A and connected to Wi-Fi.", symbol="!")
        
    launch_wsl_system()
    launch_motor_controller()
    launch_web_teleop(pi_ip)
    
    print("\n" + "=" * 68)
    if pi_ready:
        log("ALL SYSTEMS ONLINE! RViz2 + Web Controller + Motors + Arm + Camera + Pi LCD HUD Active!", symbol="SUCCESS")
    else:
        log("LOCAL VISUALIZERS LAUNCHED! (Awaiting Pi network connection).", symbol="READY")
    print("=" * 68 + "\n")

if __name__ == '__main__':
    main()
