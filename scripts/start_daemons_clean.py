import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 65)
    print("      LAUNCHING PERSISTENT SENSOR DAEMONS ON PI WITH </dev/null")
    print("=" * 65)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
    
    # 1. Kill old processes
    print("[1] Cleaning old processes...")
    ssh.exec_command("pkill -f fast_camera_server ; pkill -f rpicam ; docker exec soccer_bot_edge pkill -f bridge_scan")
    time.sleep(1)
    
    # 2. Upload latest scripts
    print("[2] Uploading latest scripts...")
    sftp = ssh.open_sftp()
    sftp.put('scripts/bridge_scan_to_laptop.py', '/home/hasan/bridge_scan_to_laptop.py')
    sftp.put('scripts/fast_camera_server.py', '/home/hasan/fast_camera_server.py')
    sftp.close()
    
    ssh.exec_command("docker cp /home/hasan/bridge_scan_to_laptop.py soccer_bot_edge:/bridge_scan_to_laptop.py")
    
    # 3. Start Camera Server with </dev/null
    print("[3] Starting Camera Server on Pi...")
    ssh.exec_command("nohup python3 -u /home/hasan/fast_camera_server.py </dev/null >/tmp/camera_server.log 2>&1 &")
    
    # 4. Start Lidar Bridge with </dev/null
    print("[4] Starting Lidar Bridge inside Docker...")
    ssh.exec_command("docker exec -d soccer_bot_edge /bin/bash -c 'source /opt/ros/jazzy/setup.bash ; nohup python3 -u /bridge_scan_to_laptop.py </dev/null >/tmp/lidar_bridge.log 2>&1 &'")
    time.sleep(3)
    
    # Check processes
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep fast_camera_server | grep -v grep ; docker exec soccer_bot_edge ps aux | grep bridge_scan | grep -v grep")
    print("\nRunning Processes on Pi:\n" + stdout.read().decode().strip())
    
    ssh.close()
    
    # 5. Socket Test from Laptop
    print("\n[5] Verifying Socket Streams from Laptop:")
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
