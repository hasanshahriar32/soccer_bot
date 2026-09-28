import socket
import json
import math
import time
import threading
import struct
import numpy as np
import cv2

PI_IP = '192.168.0.135'
LIDAR_PORT = 5000
CAMERA_PORT = 8000

# Global shared data
lidar_ranges = []
camera_frame = None
lock = threading.Lock()
running = True

def lidar_receiver():
    global lidar_ranges, running
    while running:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect((PI_IP, LIDAR_PORT))
            buffer = ""
            while running:
                data = s.recv(4096).decode('utf-8', errors='ignore')
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        if "ranges" in msg:
                            with lock:
                                lidar_ranges = msg["ranges"]
                    except:
                        pass
            s.close()
        except Exception:
            time.sleep(1.5)

def camera_receiver():
    global camera_frame, running
    while running:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect((PI_IP, CAMERA_PORT))
            
            payload_size = struct.calcsize(">L")
            data = b""
            
            while running:
                # 1. Retrieve the size of the frame
                while len(data) < payload_size:
                    packet = s.recv(4096)
                    if not packet:
                        break
                    data += packet
                if len(data) < payload_size:
                    break
                
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]
                
                # 2. Retrieve the actual frame content based on size
                while len(data) < msg_size:
                    packet = s.recv(65536)
                    if not packet:
                        break
                    data += packet
                if len(data) < msg_size:
                    break
                
                frame_data = data[:msg_size]
                data = data[msg_size:]
                
                # 3. Decode JPEG frame
                img = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    with lock:
                        camera_frame = img
            s.close()
        except Exception:
            time.sleep(1.5)

def draw_radar(w=600, h=600):
    radar = np.zeros((h, w, 3), dtype=np.uint8)
    cx, cy = w // 2, h // 2
    max_dist = 4.0 # 4 meters
    scale = (w // 2 - 40) / max_dist

    # Draw Range Rings
    for r in [1.0, 2.0, 3.0, 4.0]:
        radius_px = int(r * scale)
        cv2.circle(radar, (cx, cy), radius_px, (45, 45, 45), 1)
        cv2.putText(radar, f"{int(r)}m", (cx + 5, cy - radius_px + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1)

    # Draw Crosshairs
    cv2.line(radar, (cx, 20), (cx, h - 20), (50, 50, 50), 1)
    cv2.line(radar, (20, cy), (w - 20, cy), (50, 50, 50), 1)

    # Draw Robot Marker (Center)
    cv2.circle(radar, (cx, cy), 14, (0, 200, 255), -1)
    cv2.circle(radar, (cx, cy), 16, (255, 255, 255), 2)
    # Forward Arrow
    cv2.arrowedLine(radar, (cx, cy), (cx, cy - 35), (0, 255, 0), 2, tipLength=0.3)

    # Plot Laser Points
    with lock:
        ranges = list(lidar_ranges)

    if ranges:
        num_points = len(ranges)
        for i, dist in enumerate(ranges):
            if 0.12 < dist < max_dist:
                angle_rad = (2.0 * math.pi * i) / num_points
                # Convert polar to cartesian (0 deg is robot forward = -Y)
                px = int(cx + dist * scale * math.sin(angle_rad))
                py = int(cy - dist * scale * math.cos(angle_rad))
                
                # Color code by distance (Red = close, Yellow = med, Cyan = far)
                if dist < 0.6:
                    color = (0, 0, 255) # Red warning
                    size = 3
                elif dist < 1.5:
                    color = (0, 200, 255) # Yellow
                    size = 2
                else:
                    color = (255, 180, 50) # Cyan
                    size = 2
                cv2.circle(radar, (px, py), size, color, -1)

    cv2.putText(radar, "360 LIDAR SCAN", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    return radar

def main():
    print("=" * 60)
    print("   SOCCER BOT - LIVE LIDAR & CAMERA DASHBOARD (WINDOWS)")
    print("=" * 60)
    
    t1 = threading.Thread(target=lidar_receiver, daemon=True)
    t2 = threading.Thread(target=camera_receiver, daemon=True)
    t1.start()
    t2.start()

    cv2.namedWindow("SOCCER BOT - LIVE SENSOR DASHBOARD", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("SOCCER BOT - LIVE SENSOR DASHBOARD", 1280, 650)

    fps_timer = time.time()
    frames = 0
    fps = 0

    while True:
        radar_img = draw_radar(600, 600)

        with lock:
            if camera_frame is not None:
                cam_img = camera_frame.copy()
            else:
                cam_img = np.zeros((600, 640, 3), dtype=np.uint8)
                cv2.putText(cam_img, "CONNECTING TO PI CAMERA...", (80, 300),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

        cam_resized = cv2.resize(cam_img, (640, 600))
        cv2.putText(cam_resized, "LIVE CSI CAMERA (OV5647)", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # FPS Counter
        frames += 1
        if time.time() - fps_timer >= 1.0:
            fps = frames
            frames = 0
            fps_timer = time.time()

        cv2.putText(cam_resized, f"FPS: {fps}", (530, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

        # Combine Radar + Camera side by side
        dashboard = np.hstack([radar_img, cam_resized])

        # Bottom Status Bar
        status_bar = np.zeros((50, 1240, 3), dtype=np.uint8)
        cv2.putText(status_bar, "ROBOT STATUS: ONLINE | LIDAR: ACTIVE (Port 5000) | CAMERA: ACTIVE (Port 8000) | Press 'Q' to Exit",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        
        full_gui = np.vstack([dashboard, status_bar])

        cv2.imshow("SOCCER BOT - LIVE SENSOR DASHBOARD", full_gui)

        key = cv2.waitKey(15) & 0xFF
        if key == ord('q') or key == 27:
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
