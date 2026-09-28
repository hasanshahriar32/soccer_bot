import paramiko
import socket
import json
import time

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 65)
    print("          DEEP HARDWARE & SENSOR STREAM AUDIT")
    print("=" * 65)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
    
    # 1. Pi System & Device Node Check
    print("\n[1] Physical Devices on Pi:")
    stdin, stdout, stderr = ssh.exec_command("ls -l /dev/ttyUSB* /dev/video* 2>/dev/null ; vcgencmd get_camera 2>/dev/null || rpicam-hello --list-cameras")
    print(stdout.read().decode().strip())
    
    # 2. Check Processes on Pi Host
    print("\n[2] Camera & Background Processes on Pi Host:")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'python3|rpicam|fast_camera' | grep -v grep")
    print(stdout.read().decode().strip())
    
    # 3. Check Processes inside Docker Container
    print("\n[3] Lidar & ROS 2 Processes inside Docker:")
    stdin, stdout, stderr = ssh.exec_command("docker exec soccer_bot_edge ps aux")
    print(stdout.read().decode().strip())
    
    # 4. Check Ports listening on Pi
    print("\n[4] Listening Ports on Pi (5000 / 8000):")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlpn 2>/dev/null | grep -E '5000|8000'")
    print(stdout.read().decode().strip())
    
    ssh.close()
    
    # 5. Laptop Direct Socket Test
    print("\n[5] Laptop Socket Connection Test:")
    # Test Lidar 5000
    try:
        s = socket.socket()
        s.settimeout(2.0)
        s.connect((PI_IP, 5000))
        data = s.recv(1024)
        print(f"  -> Lidar Port 5000: OPEN! Received {len(data)} bytes")
        s.close()
    except Exception as e:
        print(f"  -> Lidar Port 5000: FAILED ({e})")
        
    # Test Camera 8000
    try:
        s = socket.socket()
        s.settimeout(2.0)
        s.connect((PI_IP, 8000))
        data = s.recv(1024)
        print(f"  -> Camera Port 8000: OPEN! Received {len(data)} bytes")
        s.close()
    except Exception as e:
        print(f"  -> Camera Port 8000: FAILED ({e})")
        
    print("\n" + "=" * 65)

if __name__ == '__main__':
    main()
