import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 65)
    print("       DEPLOYING FIXED SENSOR SERVERS TO PI (5000 & 8000)")
    print("=" * 65)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
    
    # 1. Upload files
    print("[1] Uploading scripts to Pi...")
    sftp = ssh.open_sftp()
    sftp.put('scripts/bridge_scan_to_laptop.py', '/home/hasan/bridge_scan_to_laptop.py')
    sftp.put('scripts/fast_camera_server.py', '/home/hasan/fast_camera_server.py')
    sftp.close()
    
    # 2. Copy bridge into Docker container & start it
    print("[2] Starting Lidar Bridge inside Docker Container...")
    ssh.exec_command("docker cp /home/hasan/bridge_scan_to_laptop.py soccer_bot_edge:/bridge_scan_to_laptop.py")
    ssh.exec_command("docker exec soccer_bot_edge rm -f /tmp/lidar_bridge.log")
    ssh.exec_command("docker exec -d soccer_bot_edge /bin/bash -c 'source /opt/ros/jazzy/setup.bash ; pkill -f bridge_scan ; python3 -u /bridge_scan_to_laptop.py > /tmp/lidar_bridge.log 2>&1'")
    
    # 3. Start Camera Server on Pi
    print("[3] Starting Camera Server on Pi...")
    ssh.exec_command("rm -f /tmp/camera_server.log ; pkill -f fast_camera_server ; pkill -f rpicam ; sleep 1 ; nohup python3 -u /home/hasan/fast_camera_server.py > /tmp/camera_server.log 2>&1 &")
    time.sleep(3)
    
    # Check Logs
    print("\n--- LIDAR BRIDGE LOG ---")
    s, o, e = ssh.exec_command("docker exec soccer_bot_edge cat /tmp/lidar_bridge.log")
    print(o.read().decode().strip())
    
    print("\n--- CAMERA SERVER LOG ---")
    s, o, e = ssh.exec_command("cat /tmp/camera_server.log")
    print(o.read().decode().strip())
    
    ssh.close()
    
    # 4. Verify Socket Data
    print("\n[4] Testing Socket Connections from Laptop:")
    time.sleep(1)
    # Lidar
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 5000))
        data = s.recv(1024)
        print(f"  [LIDAR 5000] -> SUCCESS! Received {len(data)} bytes of laser scan points!")
        s.close()
    except Exception as e:
        print(f"  [LIDAR 5000] -> ERROR: {e}")

    # Camera
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 8000))
        data = s.recv(1024)
        print(f"  [CAMERA 8000] -> SUCCESS! Received {len(data)} bytes of live JPEG video frames!")
        s.close()
    except Exception as e:
        print(f"  [CAMERA 8000] -> ERROR: {e}")
        
    print("=" * 65)

if __name__ == '__main__':
    main()
