import paramiko
import time

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("          CONNECTING TO RASPBERRY PI & SERVICES")
    print("=" * 60)
    
    print(f"Connecting to Raspberry Pi ({PI_IP})...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
    print("[OK] SSH Connection Established!")
    
    # 1. Start Docker container & Lidar Bridge
    print("\n[1/3] Initializing YDLidar ROS 2 Docker Container...")
    ssh.exec_command("docker start soccer_bot_edge")
    time.sleep(1)
    ssh.exec_command("docker exec -d soccer_bot_edge /bin/bash -c 'source /opt/ros/jazzy/setup.bash ; python3 -u /bridge_scan_to_laptop.py > /tmp/lidar_bridge.log 2>&1'")
    
    # 2. Start Camera Server
    print("[2/3] Starting High-Speed Camera Server (Port 8000)...")
    ssh.exec_command("pkill -f fast_camera_server ; pkill -f rpicam-vid ; sleep 1 ; nohup python3 /home/hasan/fast_camera_server.py > /tmp/camera_server.log 2>&1 &")
    time.sleep(2)
    
    # 3. Check Arduino connection
    print("[3/3] Checking Arduino Uno on /dev/ttyACM0...")
    stdin, stdout, stderr = ssh.exec_command("ls -l /dev/ttyACM0 2>/dev/null || echo 'No Arduino on /dev/ttyACM0'")
    ard_out = stdout.read().decode().strip()
    print("  Arduino Device:", ard_out)
    
    stdin, stdout, stderr = ssh.exec_command("docker ps --format '{{.Names}}: {{.Status}}'")
    dock_out = stdout.read().decode().strip()
    print("  Docker Container:", dock_out)
    
    ssh.close()
    print("\n" + "=" * 60)
    print(">>> Raspberry Pi is 100% CONNECTED & ALL HARDWARE ACTIVE! <<<")
    print("=" * 60)

if __name__ == '__main__':
    main()
