#!/usr/bin/env python3
"""
stream_from_pi.py
Listens on TCP port 8000 on this PC (192.168.0.112).
SSHs into Raspberry Pi (hasan@192.168.0.135) with password 'grammarpro'
and triggers rpicam-vid to stream live MJPEG video from the Pi camera directly to this PC!
"""

import sys
import time
import socket
import threading
import paramiko
import cv2
import numpy as np

PC_IP = "192.168.0.112"
PI_IP = "192.168.0.135"
PI_USER = "hasan"
PI_PASS = "grammarpro"
PORT = 8000

def trigger_pi_camera():
    time.sleep(1) # wait for server to start
    print(f"[SSH] Connecting to Raspberry Pi at {PI_IP}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
        print("[SSH] Connected successfully! Starting rpicam-vid stream to PC...")
        cmd = f"pkill -f rpicam-vid || true; rpicam-vid -n -t 10000 --inline -o tcp://{PC_IP}:{PORT} --codec mjpeg --width 640 --height 480 --framerate 15"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.read()
        client.close()
        print("[SSH] Camera streaming completed on Pi.")
    except Exception as e:
        print(f"[SSH] Error: {e}")

def run_pc_receiver():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', PORT))
    server_socket.listen(1)
    server_socket.settimeout(15.0)
    
    print(f"\n=======================================================")
    print(f" Listening for Raspberry Pi camera stream on port {PORT}...")
    print(f" Target Laptop IP: {PC_IP}")
    print(f" Target Pi IP:     {PI_IP}")
    print(f"=======================================================\n")
    
    # Launch Pi SSH trigger thread
    t = threading.Thread(target=trigger_pi_camera, daemon=True)
    t.start()
    
    try:
        conn, addr = server_socket.accept()
        print(f"[SUCCESS] Raspberry Pi Camera connected from {addr}!")
        
        stream_bytes = b""
        frame_count = 0
        start_time = time.time()
        
        while True:
            data = conn.recv(65536)
            if not data:
                print("Pi disconnected.")
                break
            stream_bytes += data
            
            a = stream_bytes.find(b'\xff\xd8')
            b = stream_bytes.find(b'\xff\xd9')
            
            if a != -1 and b != -1 and b > a:
                jpg = stream_bytes[a:b+2]
                stream_bytes = stream_bytes[b+2:]
                
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    frame_count += 1
                    h, w, _ = frame.shape
                    print(f"Frame #{frame_count:03d}: Received MJPEG image {w}x{h} ({len(jpg)} bytes)")
                    if frame_count >= 30:
                        print(f"\n[OK] Successfully received {frame_count} frames from Raspberry Pi!")
                        break
                        
        elapsed = time.time() - start_time
        if frame_count > 0:
            print(f"Average frame rate: {frame_count / elapsed:.1f} FPS")
            
        conn.close()
    except socket.timeout:
        print("[ERROR] Timed out waiting for Pi camera connection.")
    except Exception as e:
        print(f"[ERROR] Stream error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    run_pc_receiver()
