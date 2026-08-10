#!/usr/bin/env python3
"""
connect_and_stream_pi.py
========================
Automated connection & data streaming tool between Laptop (PC) and Raspberry Pi.

Target Pi:   hasan@192.168.0.135 (Password: grammarpro)
Local PC:    192.168.0.112
"""

import sys
import time
import socket
import threading
import paramiko

PI_IP = "192.168.0.135"
PI_USER = "hasan"
PI_PASS = "grammarpro"
PC_IP = "192.168.0.112"

def connect_ssh():
    print("=======================================================")
    print(f" Connecting to Raspberry Pi over SSH...")
    print(f" Target Pi:   {PI_USER}@{PI_IP}")
    print(f" Password:    {PI_PASS}")
    print("=======================================================")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
        print("\n[OK] SSH Connection Established!")
        
        # Check system diagnostics
        stdin, stdout, stderr = client.exec_command("uname -a; uptime; ls -l /dev/ttyUSB* /dev/video* 2>/dev/null")
        diag = stdout.read().decode().strip()
        print("\n--- Raspberry Pi System Status ---")
        print(diag)
        print("-----------------------------------")
        
        # Start Pi background bridge services
        print("\n[OK] Starting Pi Sensor Bridge & Camera Streamers...")
        cmd = (
            "sudo pkill -9 -f ydlidar_ros2_driver 2>/dev/null; "
            "pkill -9 -f python_socat 2>/dev/null; "
            "nohup python3 -u /home/hasan/python_socat.py > ~/socat.log 2>&1 & "
            "sleep 1; ps aux | grep python_socat"
        )
        stdin, stdout, stderr = client.exec_command(cmd)
        ps_out = stdout.read().decode().strip()
        print(ps_out)
        
        client.close()
        return True
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to Pi over SSH: {e}")
        return False

def test_tcp_data_stream():
    port = 5000
    print(f"\n=======================================================")
    print(f" Receiving Data Stream from Raspberry Pi on Port {port}...")
    print(f"=======================================================")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    try:
        sock.connect((PI_IP, port))
        print(f"[OK] Connected to Pi Streamer ({PI_IP}:{port})!")
        print("Listening for incoming bytes from Pi...\n")
        
        # Query YDLidar health packet
        sock.sendall(b'\xA5\x92')
        time.sleep(0.3)
        
        start_time = time.time()
        total_bytes = 0
        
        for i in range(5):
            try:
                data = sock.recv(1024)
                if not data:
                    break
                total_bytes += len(data)
                hex_rep = " ".join(f"{b:02X}" for b in data[:20])
                print(f"  --> Packet #{i+1}: Received {len(data)} bytes | Hex: [{hex_rep}...]")
            except socket.timeout:
                print("  --> Waiting for stream packets...")
                break
                
        print(f"\n[OK] Stream test complete. Received {total_bytes} bytes from Pi.")
        sock.close()
    except Exception as e:
        print(f"[ERROR] TCP Data Stream error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    if connect_ssh():
        time.sleep(1)
        test_tcp_data_stream()
