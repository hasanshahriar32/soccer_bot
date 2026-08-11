import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 65)
    print("   INSTALLING PERMANENT 24/7 SYSTEMD SERVICES ON RASPBERRY PI")
    print("=" * 65)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
    
    # 1. Upload latest scripts to /home/hasan/
    print("[1] Syncing scripts to Pi...")
    sftp = ssh.open_sftp()
    sftp.put('scripts/bridge_scan_to_laptop.py', '/home/hasan/bridge_scan_to_laptop.py')
    sftp.put('scripts/fast_camera_server.py', '/home/hasan/fast_camera_server.py')
    sftp.close()
    
    # Copy bridge into Docker container
    ssh.exec_command("docker start soccer_bot_edge")
    time.sleep(1)
    ssh.exec_command("docker cp /home/hasan/bridge_scan_to_laptop.py soccer_bot_edge:/bridge_scan_to_laptop.py")
    
    # 2. Create runner scripts on Pi
    print("[2] Creating service runner scripts...")
    lidar_runner = """#!/bin/bash
docker start soccer_bot_edge
sleep 2
docker exec soccer_bot_edge /bin/bash -c "source /opt/ros/jazzy/setup.bash && python3 -u /bridge_scan_to_laptop.py"
"""
    camera_runner = """#!/bin/bash
pkill -f rpicam-vid 2>/dev/null
exec /usr/bin/python3 -u /home/hasan/fast_camera_server.py
"""
    sftp = ssh.open_sftp()
    with sftp.file('/home/hasan/run_lidar.sh', 'w') as f:
        f.write(lidar_runner)
    with sftp.file('/home/hasan/run_camera.sh', 'w') as f:
        f.write(camera_runner)
    sftp.close()
    
    ssh.exec_command("chmod +x /home/hasan/run_lidar.sh /home/hasan/run_camera.sh")
    
    # 3. Create Systemd Services
    print("[3] Creating systemd service definitions...")
    lidar_service = """[Unit]
Description=Soccer Bot Lidar TCP Bridge Server (Port 5000)
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=hasan
ExecStart=/home/hasan/run_lidar.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    camera_service = """[Unit]
Description=Soccer Bot Camera TCP Streaming Server (Port 8000)
After=network.target

[Service]
Type=simple
User=hasan
ExecStart=/home/hasan/run_camera.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/soccer_lidar.service', 'w') as f:
        f.write(lidar_service)
    with sftp.file('/tmp/soccer_camera.service', 'w') as f:
        f.write(camera_service)
    sftp.close()
    
    # Install services with sudo
    print("[4] Installing and enabling permanent systemd services...")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S cp /tmp/soccer_lidar.service /tmp/soccer_camera.service /etc/systemd/system/")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl daemon-reload")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl enable soccer_lidar.service soccer_camera.service")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl restart soccer_lidar.service soccer_camera.service")
    
    time.sleep(4.0)
    
    # Check status
    print("\n--- SYSTEMD SERVICE STATUS ---")
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active soccer_lidar.service soccer_camera.service")
    print("Service Status:\n" + stdout.read().decode().strip())
    
    ssh.close()
    
    # 4. Verify Socket Connections
    print("\n[5] Verifying Permanent Streams from Laptop:")
    time.sleep(1)
    # Lidar
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 5000))
        data = s.recv(1024)
        print(f"  [LIDAR 5000] -> PERMANENT & ONLINE! Received {len(data)} bytes of laser scan points.")
        s.close()
    except Exception as e:
        print(f"  [LIDAR 5000] -> Error: {e}")

    # Camera
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 8000))
        data = s.recv(1024)
        print(f"  [CAMERA 8000] -> PERMANENT & ONLINE! Received {len(data)} bytes of live JPEG video.")
        s.close()
    except Exception as e:
        print(f"  [CAMERA 8000] -> Error: {e}")
        
    print("\n" + "=" * 65)
    print(">>> 24/7 PERMANENT AUTO-START CONFIGURATION COMPLETE! <<<")
    print("=" * 65)

if __name__ == '__main__':
    main()
