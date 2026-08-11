import cv2
import socket
import numpy as np
import threading
import time
import subprocess
import os

laptop_ip = '192.168.0.108'
port = 8000
running = True

def free_port_8000():
    try:
        out = subprocess.check_output('netstat -ano | findstr :8000', shell=True).decode()
        for line in out.strip().split('\n'):
            parts = line.strip().split()
            if len(parts) >= 5 and 'LISTENING' in line:
                pid = parts[-1]
                if int(pid) != os.getpid():
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
    except:
        pass

def main():
    global running
    print("Initializing Camera Viewer...")
    free_port_8000()
    time.sleep(0.5)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(1)
    print(f"Listening on 0.0.0.0:{port} for Pi camera stream...")

    window_name = "Soccer Bot - Live Camera Feed"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)

    while running:
        print("[Waiting] Waiting for incoming camera stream from Pi...")
        conn, addr = server.accept()
        print(f"[Connected] Pi streaming from {addr}!")
        
        stream_bytes = b''
        last_frame_time = time.time()
        fps = 0
        frame_counter = 0

        while running:
            try:
                data = conn.recv(65536)
                if not data:
                    print("[Disconnected] Connection lost, reconnecting...")
                    break
                stream_bytes += data
                
                a = stream_bytes.find(b'\xff\xd8')
                b = stream_bytes.find(b'\xff\xd9')
                
                if a != -1 and b != -1 and b > a:
                    jpg = stream_bytes[a:b+2]
                    stream_bytes = stream_bytes[b+2:]
                    
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        frame_counter += 1
                        now = time.time()
                        if now - last_frame_time >= 1.0:
                            fps = frame_counter
                            frame_counter = 0
                            last_frame_time = now

                        # HUD text
                        h, w = frame.shape[:2]
                        cv2.putText(frame, f"LIVE CAMERA | {w}x{h} | {fps} FPS", (15, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)

                        cv2.imshow(window_name, frame)
                        key = cv2.waitKey(1) & 0xFF
                        if key == 27 or key == ord('q'):
                            running = False
                            break
            except Exception as e:
                break
                
        conn.close()

    server.close()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
