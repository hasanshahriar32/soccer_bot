import paramiko
import time
import socket
import json

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("        RESTARTING PI LIDAR DOCKER CONTAINER")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
    
    print("[1] Restarting Docker container 'soccer_bot_edge'...")
    ssh.exec_command("docker restart soccer_bot_edge")
    time.sleep(4.0)
    
    print("[2] Launching clean Lidar TCP Bridge...")
    ssh.exec_command("docker exec -d soccer_bot_edge /bin/bash -c 'source /opt/ros/jazzy/setup.bash ; python3 -u /bridge_scan_to_laptop.py > /tmp/lidar_bridge.log 2>&1'")
    time.sleep(3.0)
    
    stdin, stdout, stderr = ssh.exec_command("docker exec soccer_bot_edge cat /tmp/lidar_bridge.log")
    print("Bridge Startup Log:\n" + stdout.read().decode().strip())
    ssh.close()
    
    print("\n[3] Verifying Live Scan Range Data on Port 5000...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(4.0)
    s.connect((PI_IP, 5000))
    buffer = ""
    for _ in range(20):
        data = s.recv(4096).decode('utf-8', errors='ignore')
        if not data: break
        buffer += data
        if "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line:
                try:
                    msg = json.loads(line)
                    ranges = msg.get("ranges", [])
                    valid = [r for r in ranges if 0.15 < r < 8.0]
                    if valid:
                        print(f"[SUCCESS] 360° LIDAR Active! Received {len(ranges)} ray points ({len(valid)} valid obstacles detected around robot)!")
                        break
                except:
                    pass
    s.close()
    print("=" * 60)

if __name__ == '__main__':
    main()
