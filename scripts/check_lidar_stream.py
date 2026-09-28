import paramiko
import socket
import json
import time

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("        AUDITING 360° LIDAR STREAM ON PI & LAPTOP")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
    
    print("\n[Step 1] Checking Pi Docker Container & YDLIDAR Driver:")
    stdin, stdout, stderr = ssh.exec_command("docker ps --format '{{.Names}}: {{.Status}}'")
    print("  Docker Container:", stdout.read().decode().strip())
    
    stdin, stdout, stderr = ssh.exec_command("docker exec soccer_bot_edge ps aux | grep ydlidar")
    print("  YDLidar Driver Process:\n" + stdout.read().decode().strip())
    
    print("\n[Step 2] Restarting Lidar TCP Bridge on Pi (Port 5000)...")
    ssh.exec_command("docker exec -d soccer_bot_edge /bin/bash -c 'source /opt/ros/jazzy/setup.bash ; pkill -f bridge_scan ; python3 -u /bridge_scan_to_laptop.py > /tmp/lidar_bridge.log 2>&1'")
    time.sleep(2.0)
    
    stdin, stdout, stderr = ssh.exec_command("docker exec soccer_bot_edge cat /tmp/lidar_bridge.log | tail -n 5")
    print("  Bridge Log:\n" + stdout.read().decode().strip())
    ssh.close()
    
    print("\n[Step 3] Testing Live Socket Data from Laptop (Port 5000)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.0)
        s.connect((PI_IP, 5000))
        buffer = ""
        received = False
        start = time.time()
        while time.time() - start < 3.0:
            data = s.recv(4096).decode('utf-8', errors='ignore')
            if not data: break
            buffer += data
            if "\n" in buffer:
                line, _ = buffer.split("\n", 1)
                msg = json.loads(line.strip())
                ranges = msg.get("ranges", [])
                valid = [r for r in ranges if 0.1 < r < 10.0]
                print(f"  [SUCCESS] Received LaserScan from Pi! Total points: {len(ranges)}, Valid obstacles: {len(valid)}")
                received = True
                break
        s.close()
        if not received:
            print("  [WARN] No complete scan packet received within 3s.")
    except Exception as e:
        print(f"  [FAIL] Socket connection failed: {e}")
        
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
