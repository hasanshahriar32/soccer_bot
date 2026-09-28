import cv2
import socket
import json
import math
import numpy as np
import threading
import time

latest_scan = {}
lock = threading.Lock()
running = True
pi_ip = '192.168.0.135'
lidar_port = 5000

def lidar_client():
    global latest_scan, running
    while running:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect((pi_ip, lidar_port))
            print(f"[SUCCESS] Connected to Pi Lidar at {pi_ip}:{lidar_port}")
            buffer = ""
            while running:
                data = s.recv(4096).decode('utf-8', errors='ignore')
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line and line.startswith("{"):
                        try:
                            scan_data = json.loads(line)
                            with lock:
                                latest_scan = scan_data
                        except:
                            pass
            s.close()
        except Exception as e:
            time.sleep(1)

def main():
    global running
    print("Starting Dedicated High-Performance Lidar Radar...")
    
    t = threading.Thread(target=lidar_client, daemon=True)
    t.start()

    window_name = "YDLIDAR - Live 360 Scan Radar"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 750, 750)

    size = 700
    cx, cy = size // 2, size // 2
    max_range_m = 4.0
    scale = (cx - 40) / max_range_m

    last_time = time.time()
    fps = 0

    while True:
        img = np.zeros((size, size, 3), dtype=np.uint8)
        img[:] = (20, 20, 25)

        # Range circles & labels
        for r in [1.0, 2.0, 3.0, 4.0]:
            r_px = int(r * scale)
            cv2.circle(img, (cx, cy), r_px, (55, 55, 65), 1, cv2.LINE_AA)
            cv2.putText(img, f"{int(r)}m", (cx + 5, cy - r_px + 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 140), 1, cv2.LINE_AA)

        # Cardinal axis
        cv2.line(img, (cx, 20), (cx, size - 20), (45, 45, 55), 1, cv2.LINE_AA)
        cv2.line(img, (20, cy), (size - 20, cy), (45, 45, 55), 1, cv2.LINE_AA)
        cv2.putText(img, "FRONT (0 deg)", (cx - 45, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img, "BACK (180 deg)", (cx - 45, size - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA)

        # Robot center
        cv2.circle(img, (cx, cy), 10, (0, 220, 0), -1, cv2.LINE_AA)
        cv2.circle(img, (cx, cy), 12, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.arrowedLine(img, (cx, cy), (cx, cy - 35), (0, 255, 255), 3, tipLength=0.35)

        with lock:
            current_points = dict(latest_scan)

        point_count = 0
        closest_dist = 999.0
        closest_angle = 0

        for angle_str, dist_mm in current_points.items():
            try:
                angle_deg = float(angle_str)
                dist_m = float(dist_mm) / 1000.0
                if 0.08 < dist_m <= max_range_m:
                    rad = math.radians(angle_deg)
                    px = int(cx + dist_m * math.sin(rad) * scale)
                    py = int(cy - dist_m * math.cos(rad) * scale)

                    if 0 <= px < size and 0 <= py < size:
                        cv2.circle(img, (px, py), 4, (0, 0, 255), -1, cv2.LINE_AA)
                        cv2.circle(img, (px, py), 1, (255, 255, 255), -1, cv2.LINE_AA)
                        point_count += 1

                        if dist_m < closest_dist:
                            closest_dist = dist_m
                            closest_angle = angle_deg
            except:
                pass

        curr_time = time.time()
        fps = int(1.0 / (curr_time - last_time + 1e-6))
        last_time = curr_time

        cv2.rectangle(img, (15, 15), (280, 115), (35, 35, 45), -1)
        cv2.rectangle(img, (15, 15), (280, 115), (70, 70, 90), 1)

        cv2.putText(img, f"YDLIDAR LIVE RADAR", (25, 38), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, f"Points Detected: {point_count}", (25, 62), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 0), 1, cv2.LINE_AA)
        
        if closest_dist < 999.0:
            cv2.putText(img, f"Closest: {closest_dist:.2f}m @ {int(closest_angle)} deg", (25, 84), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 180, 255), 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "Searching for points...", (25, 84), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 255), 1, cv2.LINE_AA)

        cv2.putText(img, f"Status: STREAMING | {fps} FPS", (25, 104), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1, cv2.LINE_AA)

        cv2.imshow(window_name, img)

        key = cv2.waitKey(20) & 0xFF
        if key == 27 or key == ord('q'):
            break

    running = False
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
