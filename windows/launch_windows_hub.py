#!/usr/bin/env python3
"""
====================================================================
           SOCCER BOT - ROBUST AUTO-HEALING MASTER LAUNCHER
====================================================================
Description:
    Master launcher for Windows & WSL setup on user PC (taufi).
    Features multi-subnet auto-discovery for Raspberry Pi IP.
"""

import time
import subprocess
import os
import sys
import socket
import concurrent.futures

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

DEFAULT_PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

WSL_BASE = "/mnt/c/Users/taufi/Desktop/soccer_bot"
RVIZ_CONFIG = f"{WSL_BASE}/scripts/soccer_bot.rviz"
IS_WINDOWS = sys.platform == 'win32'

def log(msg, symbol="*"):
    print(f"[{symbol}] {msg}", flush=True)

def is_vcxsrv_running():
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq vcxsrv.exe"', shell=True).decode('utf-8', errors='ignore')
        return 'vcxsrv.exe' in out.lower()
    except:
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
    except:
        pass
    return None

def find_pi_ip():
    if test_ssh_ip(DEFAULT_PI_IP):
        return DEFAULT_PI_IP
        
    subnets = ['192.168.0', '192.168.1', '192.168.43', '172.20.10', '192.168.137']
    log("Scanning local networks (Wi-Fi / Hotspot) for Raspberry Pi...", symbol="SEARCH")
    
    targets = [f"{sub}.{i}" for sub in subnets for i in range(1, 255)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
        results = ex.map(test_ssh_ip, targets)
        for ip in results:
            if ip and not ip.endswith('.1'):
                log(f"Auto-discovered Raspberry Pi at IP: {ip}", symbol="FOUND")
                return ip
    return None

def launch_pi_sensors(pi_ip):
    log(f"Connecting to Raspberry Pi at {pi_ip}...", symbol="1/3")
    if HAS_PARAMIKO:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(pi_ip, username=PI_USER, password=PI_PASS, timeout=5)
            
            # Stop conflicting Pipewire / Wireplumber camera locks on Pi
            ssh.exec_command("systemctl --user stop wireplumber pipewire 2>/dev/null")
            ssh.exec_command("pkill -9 -f rpicam ; pkill -9 -f python_socat.py")
            time.sleep(1.0)
            
            ssh.exec_command("nohup python3 ~/python_socat.py > ~/socat.log 2>&1 &")
            ssh.exec_command("nohup bash ~/start_rpicam.sh > ~/rpicam.log 2>&1 &")
            time.sleep(2.0)
            
            log(f"Pi Lidar (5000) & Native Camera (8088) active at {pi_ip}!", symbol="OK")
            ssh.close()
            return True
        except Exception as err:
            log(f"Pi SSH connection error: {err}", symbol="!")
            return False
    return False

def launch_wsl_system():
    log("Launching ROS 2 Sensor Hubs & RViz2 GUI in WSL...", symbol="2/3")
    
    rviz_cmd = f"bash {WSL_BASE}/scripts/launch_rviz.sh"
    if IS_WINDOWS:
        subprocess.Popen(f'wsl -d Ubuntu -- bash -c "{rviz_cmd}"', shell=True)
    else:
        subprocess.Popen(f'bash -c "{rviz_cmd}"', shell=True)

def main():
    print("=" * 65)
    print("         SOCCER BOT - MASTER SYSTEM LAUNCHER         ")
    print("=" * 65)
    
    check_and_start_vcxsrv()
    
    custom_ip = sys.argv[1] if len(sys.argv) > 1 else None
    pi_ip = custom_ip or find_pi_ip()
    
    pi_ready = False
    if pi_ip:
        pi_ready = launch_pi_sensors(pi_ip)
    else:
        log("Raspberry Pi (192.168.0.135) is currently OFFLINE or unreachable.", symbol="!")
        log("--> Check: 1. Power on Pi. 2. Verify Wi-Fi / Hotspot connection.", symbol="!")
        
    launch_wsl_system()
    
    print("\n" + "=" * 65)
    if pi_ready:
        log(f"ALL SYSTEMS ONLINE! RViz2 GUI is running with LIVE SENSORS.", symbol="SUCCESS")
    else:
        log("LOCAL VISUALIZER OPEN! (Turn on Pi & connect to Wi-Fi to stream live data).", symbol="READY")
    print("=" * 65 + "\n")

if __name__ == '__main__':
    main()
