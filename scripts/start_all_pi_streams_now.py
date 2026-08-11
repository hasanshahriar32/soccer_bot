import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("    STARTING ALL SENSOR STREAMS DIRECTLY ON PI")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)

    # 1. Start Docker container
    print("[1] Starting Docker soccer_bot_edge container...")
    ssh.exec_command("docker start soccer_bot_edge")
    time.sleep(2.0)

    # 2. Upload latest scripts to Pi & Docker
    print("[2] Uploading scripts...")
    sftp = ssh.open_sftp()
    sftp.put('scripts/bridge_scan_to_laptop.py', '/home/hasan/bridge_scan_to_laptop.py')
    sftp.put('scripts/fast_camera_server.py', '/home/hasan/fast_camera_server.py')
    sftp.put('motor_control/motor_server.py', '/home/hasan/motor_server.py')
    sftp.close()

    ssh.exec_command("docker cp /home/hasan/bridge_scan_to_laptop.py soccer_bot_edge:/bridge_scan_to_laptop.py")

    # 3. Start Lidar Bridge inside Docker
    print("[3] Starting Lidar Bridge inside Docker container...")
    ssh.exec_command("docker exec -d soccer_bot_edge /bin/bash -c 'source /opt/ros/jazzy/setup.bash ; pkill -f bridge_scan ; nohup python3 -u /bridge_scan_to_laptop.py </dev/null >/tmp/lidar_bridge.log 2>&1 &'")

    # 4. Start Camera Server on Pi
    print("[4] Starting Camera Server on Pi...")
    ssh.exec_command("pkill -f fast_camera_server ; pkill -f rpicam ; sleep 1 ; nohup python3 -u /home/hasan/fast_camera_server.py </dev/null >/tmp/camera_server.log 2>&1 &")

    # 5. Start Motor Server on Pi
    print("[5] Starting Motor Server on Pi...")
    ssh.exec_command("pkill -f motor_server ; fuser -k 9000/tcp ; sleep 1 ; nohup python3 -u /home/hasan/motor_server.py </dev/null >/tmp/motor_server.log 2>&1 &")

    time.sleep(4.0)

    # Check processes
    print("\n--- ACTIVE PROCESSES ON PI ---")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'fast_camera|motor_server' | grep -v grep ; docker exec soccer_bot_edge ps aux | grep -E 'ydlidar|bridge_scan' | grep -v grep")
    print(stdout.read().decode().strip())

    ssh.close()

    # 6. Test Socket Streams from Laptop
    print("\n[6] Verifying Live Socket Connections from Laptop:")
    # 5000 (Lidar)
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 5000))
        data = s.recv(1024)
        print(f"  [LIDAR 5000]  -> SUCCESS! Streaming laser scan data ({len(data)} bytes).")
        s.close()
    except Exception as e:
        print(f"  [LIDAR 5000]  -> Error: {e}")

    # 8000 (Camera)
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 8000))
        data = s.recv(1024)
        print(f"  [CAMERA 8000] -> SUCCESS! Streaming live JPEG frames ({len(data)} bytes).")
        s.close()
    except Exception as e:
        print(f"  [CAMERA 8000] -> Error: {e}")

    # 9000 (Motors)
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 9000))
        s.sendall(b'S')
        print(f"  [MOTORS 9000] -> SUCCESS! Motor controller is ONLINE & ready.")
        s.close()
    except Exception as e:
        print(f"  [MOTORS 9000] -> Error: {e}")

    print("=" * 60)

if __name__ == '__main__':
    main()
