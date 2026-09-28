import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 65)
    print("      STARTING PERSISTENT SENSOR DAEMONS ON PI (5000 & 8000)")
    print("=" * 65)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
    
    # 1. Start Docker Lidar Bridge
    print("[1] Starting Docker Lidar Bridge on Port 5000...")
    ssh.exec_command("docker start soccer_bot_edge")
    time.sleep(1)
    ssh.exec_command("docker exec -d soccer_bot_edge /bin/bash -c 'source /opt/ros/jazzy/setup.bash ; pkill -f bridge_scan ; python3 -u /bridge_scan_to_laptop.py > /tmp/lidar_bridge.log 2>&1'")
    
    # 2. Start Camera Server
    print("[2] Starting High-Speed Camera Server on Port 8000...")
    ssh.exec_command("pkill -f fast_camera_server ; pkill -f rpicam ; sleep 1 ; nohup python3 /home/hasan/fast_camera_server.py > /tmp/camera_server.log 2>&1 &")
    time.sleep(3)
    
    # 3. Verify listening ports
    stdin, stdout, stderr = ssh.exec_command("netstat -tlpn 2>/dev/null | grep -E '5000|8000'")
    ports = stdout.read().decode().strip()
    print("Listening Ports:\n" + (ports or "No ports detected via netstat yet"))
    
    ssh.close()
    
    # 4. Socket Verification from Laptop
    print("\n[3] Testing Laptop Socket Streams:")
    time.sleep(1)
    # Lidar
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 5000))
        data = s.recv(1024)
        print(f"  [LIDAR 5000] -> SUCCESS! Received {len(data)} bytes of laser scan data.")
        s.close()
    except Exception as e:
        print(f"  [LIDAR 5000] -> ERROR: {e}")

    # Camera
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 8000))
        data = s.recv(1024)
        print(f"  [CAMERA 8000] -> SUCCESS! Received {len(data)} bytes of camera frame data.")
        s.close()
    except Exception as e:
        print(f"  [CAMERA 8000] -> ERROR: {e}")
        
    print("=" * 65)

if __name__ == '__main__':
    main()
