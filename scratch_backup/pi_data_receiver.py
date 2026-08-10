#!/usr/bin/env python3
"""
pi_data_receiver.py
Connects to Raspberry Pi (hasan@192.168.0.135) over SSH & TCP,
starts the data streamer on the Pi, and receives data stream on this PC.
"""

import sys
import time
import socket
import paramiko
import cv2
import numpy as np

PI_IP = "192.168.0.135"
PI_USER = "hasan"
PI_PASS = "grammarpro"

def run_remote_streamer():
    print(f"Connecting to Raspberry Pi ({PI_IP}) via SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
        print("[OK] SSH Connection Successful!")
        # Launch edge_node.py in background
        cmd = "pkill -f edge_node; nohup python3 -u ~/edge_node.py > ~/camera.log 2>&1 & sleep 1; ps aux | grep edge_node"
        stdin, stdout, stderr = client.exec_command(cmd)
        print("Pi Edge Process:\n", stdout.read().decode())
        client.close()
        return True
    except Exception as e:
        print(f"SSH Error: {e}")
        return False

def receive_camera_stream():
    port = 5001
    print(f"Connecting to Pi Camera Stream on {PI_IP}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    try:
        sock.connect((PI_IP, port))
        print("[OK] CONNECTED TO PI CAMERA STREAM!")
        print("Receiving live video frames from Raspberry Pi...\n")
        
        payload_size = 4
        data = b""
        import struct
        
        frame_count = 0
        start_time = time.time()
        
        for _ in range(50): # receive 50 frames
            while len(data) < payload_size:
                packet = sock.recv(4096)
                if not packet: break
                data += packet
            if len(data) < payload_size: break
            
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            
            while len(data) < msg_size:
                data += sock.recv(4096)
                
            frame_data = data[:msg_size]
            data = data[msg_size:]
            
            frame_count += 1
            print(f"Received Frame #{frame_count}: {len(frame_data)} bytes")
            time.sleep(0.05)
            
        fps = frame_count / (time.time() - start_time)
        print(f"\n[OK] SUCCESS! Received {frame_count} live frames from Pi at {fps:.1f} FPS.")
    except Exception as e:
        print(f"Stream Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    if run_remote_streamer():
        time.sleep(2)
        receive_camera_stream()
