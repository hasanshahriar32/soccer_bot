#!/usr/bin/env python3
"""
====================================================================
  SOCCER BOT - MOBILE PHONE WEB TELEOP, AUTOPILOT & SLAM CONTROLLER
====================================================================
Accessible from any phone browser on the same Wi-Fi:
    http://192.168.0.122:5050

Features:
  1. Dual View Modes:
     - 📷 Live Low-Latency Camera Feed with AI ball crosshair
     - 🗺️ 2D LiDAR SLAM Occupancy Map with robot pose & obstacles
  2. Responsive Touch D-Pad with Hold-to-Drive & Auto-Brake on release
  3. One-Touch Autonomous Ball Follower (Autopilot with LiDAR sync)
  4. Automatic Proximity Stop at 35 cm for Object / Ball Pickup
  5. Live Telemetry HUD: LiDAR health, SLAM status, Distance, Bearing
  6. Smooth Speed Control Presets (Slow, Cruise, Fast, Sport)
====================================================================
"""

import os
import sys
import time
import math
import socket
import threading
import json
import struct
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import cv2
import numpy as np

# ROS 2 Jazzy imports
try:
    import rclpy
    from rclpy.node import Node as RosNode
    from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
    from sensor_msgs.msg import Image as RosImage, LaserScan
    from geometry_msgs.msg import Point as RosPoint, PoseStamped
    from nav_msgs.msg import OccupancyGrid
    from cv_bridge import CvBridge
    HAS_ROS2 = True
except ImportError:
    HAS_ROS2 = False

PI_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.135"
PI_MOTOR_PORT = 9000
PI_ARM_PORT = 9001
WEB_PORT = 5050

# Global Robot State
class RobotState:
    def __init__(self):
        self.lock = threading.Lock()
        self.sock = None
        self.wifi_connected = False
        self.current_action = "STOPPED"
        self.speed = 120 # Default smooth cruise speed (PWM)
        
        # Ball Tracking State
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_dist = -1.0
        self.ball_time = 0.0
        self.ball_tracked = False
        
        # Autopilot State
        self.autopilot_active = False
        self.autopilot_status = "IDLE (Manual Mode)"
        
        # Camera Frame
        self.latest_jpeg = None
        self.last_frame_time = 0.0

        # LiDAR & SLAM State
        self.laser_time = 0.0
        self.latest_scan = None
        self.raw_map = None
        self.map_time = 0.0
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0

        # 4-DOF Robotic Arm State (Port 9001)
        self.arm_connected = False
        self.arm_base = 0
        self.arm_shoulder = 0
        self.arm_albo = 0
        self.arm_gripper = 180
        self.arm_status_msg = "READY"
        self.arm_last_update = 0.0

state = RobotState()

# ====================================================================
# ROBOTIC ARM TCP CLIENT (Communicates with Pi Port 9001)
# ====================================================================
arm_cmd_lock = threading.Lock()

def send_arm_command(cmd_dict, timeout=10.0):
    try:
        with arm_cmd_lock:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(timeout)
            sock.connect((PI_IP, PI_ARM_PORT))
            payload = json.dumps(cmd_dict) + "\n"
            sock.sendall(payload.encode('utf-8'))
            resp_data = sock.recv(2048).decode('utf-8')
            sock.close()
            resp = json.loads(resp_data.strip())
            with state.lock:
                state.arm_connected = resp.get("connected", True)
                if "base" in resp:
                    state.arm_base = resp["base"]
                if "shoulder" in resp:
                    state.arm_shoulder = resp["shoulder"]
                if "albo" in resp:
                    state.arm_albo = resp["albo"]
                if "gripper" in resp:
                    state.arm_gripper = resp["gripper"]
                state.arm_status_msg = resp.get("response", resp.get("status", "OK"))
                state.arm_last_update = time.time()
            return resp
    except Exception as e:
        with state.lock:
            state.arm_connected = False
            state.arm_status_msg = f"ERR: {e}"
        return {"status": "ERR", "msg": str(e), "connected": False}

def arm_status_poller():
    time.sleep(1.0)
    while True:
        try:
            send_arm_command({"action": "status"}, timeout=2.0)
        except Exception:
            pass
        time.sleep(2.0)

threading.Thread(target=arm_status_poller, daemon=True).start()

def run_base_sweep_test():
    def _worker():
        print("[ARM] Starting Base Servo Sweep Test (0 -> 45 -> 90 -> 135 -> 90 -> 45 -> 0)...", flush=True)
        for angle in [0, 45, 90, 135, 90, 45, 0]:
            send_arm_command({"action": "joint", "joint": "B", "angle": angle}, timeout=6.0)
            time.sleep(0.5)
        print("[ARM] Base Servo Sweep Test Completed!", flush=True)
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

# ====================================================================
# MOTOR TCP CLIENT (Communicates with Pi Port 9000)
# ====================================================================
def motor_client_worker():
    while True:
        with state.lock:
            s = state.sock
        if s is None:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(2.0)
                sock.connect((PI_IP, PI_MOTOR_PORT))
                with state.lock:
                    state.sock = sock
                    state.wifi_connected = True
                print(f"[MOTOR CLIENT] Connected to Pi Motor Server at {PI_IP}:{PI_MOTOR_PORT}!", flush=True)
            except Exception:
                with state.lock:
                    state.sock = None
                    state.wifi_connected = False
                time.sleep(1.5)
        else:
            # Active liveness check
            try:
                s.sendall(b'\n')
                time.sleep(1.0)
            except Exception:
                with state.lock:
                    try:
                        s.close()
                    except Exception:
                        pass
                    state.sock = None
                    state.wifi_connected = False
                time.sleep(1.0)

threading.Thread(target=motor_client_worker, daemon=True).start()

def send_motor_command(action, speed=None):
    with state.lock:
        state.current_action = action
        sock = state.sock

    if action in ['F', 'B', 'L', 'R', 'S']:
        pkt = f"{action}\n"
    else:
        pkt = "S\n"

    if sock:
        try:
            sock.sendall(pkt.encode('utf-8'))
        except Exception as e:
            print(f"[MOTOR SEND ERR] {e}", flush=True)
            with state.lock:
                state.sock = None
                state.wifi_connected = False

# ====================================================================
# AUTOPILOT / AUTONOMOUS BALL CHASER LOOP
# ====================================================================
def autopilot_loop():
    while True:
        if state.autopilot_active:
            now = time.time()
            with state.lock:
                tracked = (now - state.ball_time) < 1.2 and state.ball_dist > 0
                dist = state.ball_dist
                lat = state.ball_y

            if tracked:
                if dist <= 0.35:
                    send_motor_command('S')
                    with state.lock:
                        state.autopilot_status = f"🎯 BALL REACHED ({dist:.2f}m)! READY FOR PICKUP"
                else:
                    if lat > 0.12:
                        send_motor_command('L')
                        with state.lock:
                            state.autopilot_status = f"🔄 ALIGNING: Turning Left (Dist: {dist:.2f}m)"
                    elif lat < -0.12:
                        send_motor_command('R')
                        with state.lock:
                            state.autopilot_status = f"🔄 ALIGNING: Turning Right (Dist: {dist:.2f}m)"
                    else:
                        send_motor_command('F')
                        with state.lock:
                            state.autopilot_status = f"🚀 APPROACHING: Driving to Ball ({dist:.2f}m)"
            else:
                send_motor_command('S')
                with state.lock:
                    state.autopilot_status = "🔍 SEARCHING: No Ball In Sight..."
        time.sleep(0.08)

threading.Thread(target=autopilot_loop, daemon=True).start()

# ====================================================================
# ROS 2 SUBSCRIBER THREAD (Camera, Ball Position, Map, Pose, LiDAR)
# ====================================================================
def ros2_subscriber_worker():
    if not HAS_ROS2:
        return
    try:
        if not rclpy.ok():
            rclpy.init()
        node = RosNode('web_teleop_hub_node')
        bridge = CvBridge()

        def image_cb(msg: RosImage):
            try:
                frame = bridge.imgmsg_to_cv2(msg, "bgr8")
                h, w = frame.shape[:2]
                
                # Crosshair
                cv2.drawMarker(frame, (w // 2, h // 2), (0, 229, 255), cv2.MARKER_CROSS, 20, 1)

                with state.lock:
                    tracked = (time.time() - state.ball_time) < 1.2 and state.ball_dist > 0
                    dist = state.ball_dist
                    lat = state.ball_y
                    auto = state.autopilot_active

                if tracked:
                    deg = math.degrees(math.atan2(lat, max(0.01, state.ball_x)))
                    hud_text = f"BALL: {dist:.2f}m | {deg:+.1f} deg"
                    cv2.putText(frame, hud_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.circle(frame, (w // 2 + int(lat * 150), h // 2), 28, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "SEARCHING BALL...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1)

                mode_text = "[AUTOPILOT ACTIVE]" if auto else "[MANUAL TELEOP]"
                mode_color = (0, 255, 0) if auto else (255, 200, 0)
                cv2.putText(frame, mode_text, (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, mode_color, 1)

                ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ret:
                    with state.lock:
                        state.latest_jpeg = buf.tobytes()
                        state.last_frame_time = time.time()
            except Exception:
                pass

        def ball_cb(msg: RosPoint):
            with state.lock:
                state.ball_x = msg.x
                state.ball_y = msg.y
                state.ball_dist = msg.z
                state.ball_time = time.time()
                state.ball_tracked = (msg.z > 0)

        def scan_cb(msg: LaserScan):
            with state.lock:
                state.laser_time = time.time()
                state.latest_scan = msg

        map_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )

        def map_cb(msg: OccupancyGrid):
            with state.lock:
                state.raw_map = msg
                state.map_time = time.time()

        def pose_cb(msg: PoseStamped):
            q = msg.pose.orientation
            t3 = +2.0 * (q.w * q.z + q.x * q.y)
            t4 = +1.0 - 2.0 * (q.y * q.y + q.z * q.z)
            yaw = math.degrees(math.atan2(t3, t4))
            with state.lock:
                state.robot_x = msg.pose.position.x
                state.robot_y = msg.pose.position.y
                state.robot_yaw = yaw

        node.create_subscription(RosImage, '/image_raw', image_cb, 5)
        node.create_subscription(RosPoint, '/ball_position', ball_cb, 10)
        node.create_subscription(LaserScan, '/scan', scan_cb, 10)
        node.create_subscription(OccupancyGrid, '/map', map_cb, map_qos)
        node.create_subscription(PoseStamped, '/robot_map_pose', pose_cb, 10)

        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
    except Exception as e:
        print(f"[ROS2 WORKER ERR] {e}", flush=True)

threading.Thread(target=ros2_subscriber_worker, daemon=True).start()

# Universal Camera Stream Worker (Supports both HTTP MJPEG from detect_live_picamera2 and TCP socket from fast_camera_server)
def universal_camera_worker():
    payload_size = struct.calcsize(">L")
    while True:
        # Check if ROS2 is already providing fresher frames
        with state.lock:
            ros2_fresh = (time.time() - state.last_frame_time) < 0.5 and getattr(state, 'ros2_has_camera', False)
        if ros2_fresh:
            time.sleep(0.3)
            continue

        # Strategy A: HTTP MJPEG Stream (detect_live_picamera2.py on /video or /)
        http_success = False
        try:
            req = urllib.request.Request(f"http://{PI_IP}:8000/video")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                stream_bytes = b""
                while True:
                    with state.lock:
                        if (time.time() - state.last_frame_time) < 0.5 and getattr(state, 'ros2_has_camera', False):
                            break
                    chunk = resp.read(16384)
                    if not chunk:
                        break
                    stream_bytes += chunk
                    a = stream_bytes.find(b'\xff\xd8')
                    b = stream_bytes.find(b'\xff\xd9', a + 2) if a != -1 else -1
                    if a != -1 and b != -1:
                        jpg = stream_bytes[a:b+2]
                        stream_bytes = stream_bytes[b+2:]
                        with state.lock:
                            state.latest_jpeg = jpg
                            state.last_frame_time = time.time()
                        http_success = True
        except Exception:
            pass

        if http_success:
            continue

        # Strategy B: Raw TCP size-prefixed socket (fast_camera_server.py)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.settimeout(3.0)
            s.connect((PI_IP, 8000))
            data = b""
            while True:
                with state.lock:
                    if (time.time() - state.last_frame_time) < 0.5 and getattr(state, 'ros2_has_camera', False):
                        break

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

                while len(data) < msg_size:
                    packet = s.recv(65536)
                    if not packet:
                        break
                    data += packet
                if len(data) < msg_size:
                    break

                frame_data = bytes(data[:msg_size])
                data = data[msg_size:]

                with state.lock:
                    state.latest_jpeg = frame_data
                    state.last_frame_time = time.time()
            s.close()
        except Exception:
            time.sleep(1.0)

threading.Thread(target=universal_camera_worker, daemon=True).start()

def get_current_camera_frame():
    with state.lock:
        if state.latest_jpeg and (time.time() - state.last_frame_time) < 1.5:
            return state.latest_jpeg

    # Synthetic Standby Frame (480x240)
    frame = np.zeros((240, 480, 3), dtype=np.uint8)
    frame[:] = (14, 18, 26)
    cv2.putText(frame, "CONNECTING TO CAMERA...", (110, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 229, 255), 2)
    cv2.putText(frame, f"Target: http://{PI_IP}:8000/video", (130, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (139, 148, 158), 1)
    ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return buf.tobytes() if ret else b''

def render_slam_map_frame():
    with state.lock:
        map_msg = state.raw_map
        scan_msg = state.latest_scan
        rx = state.robot_x
        ry = state.robot_y
        ryaw = state.robot_yaw
        bx = state.ball_x
        by = state.ball_y
        b_tracked = state.ball_tracked
        lidar_fresh = (time.time() - state.laser_time) < 2.5

    OUT_W, OUT_H = 480, 240
    if map_msg is None:
        frame = np.zeros((OUT_H, OUT_W, 3), dtype=np.uint8)
        frame[:] = (10, 14, 23)
        cx, cy = OUT_W // 2, OUT_H // 2

        if scan_msg is not None and lidar_fresh:
            scale = 45.0 # pixels per meter (~2.5m range)
            for r_m in [0.5, 1.0, 1.5, 2.0]:
                r_px = int(r_m * scale)
                cv2.circle(frame, (cx, cy), r_px, (25, 38, 55), 1)
                cv2.putText(frame, f"{r_m}m", (cx + r_px + 2, cy - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (70, 95, 120), 1)

            cv2.line(frame, (cx, 15), (cx, OUT_H - 15), (25, 38, 55), 1)
            cv2.line(frame, (cx - 120, cy), (cx + 120, cy), (25, 38, 55), 1)
            cv2.putText(frame, "FWD", (cx - 12, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 229, 255), 1)

            angle = scan_msg.angle_min
            for r in scan_msg.ranges:
                if scan_msg.range_min <= r <= scan_msg.range_max and r < 3.0:
                    px = int(cx - (r * math.sin(angle)) * scale)
                    py = int(cy - (r * math.cos(angle)) * scale)
                    if 0 <= px < OUT_W and 0 <= py < OUT_H:
                        frame[py, px] = (0, 240, 255)
                angle += scan_msg.angle_increment

            pts = np.array([[cx, cy - 8], [cx - 6, cy + 6], [cx + 6, cy + 6]], np.int32)
            cv2.fillPoly(frame, [pts], (0, 229, 255))
            cv2.putText(frame, "RADAR: 360 DEG ACTIVE", (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 180), 1)
            cv2.putText(frame, "SLAM: Building Grid...", (12, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 200, 0), 1)
        else:
            lidar_str = "LiDAR: 🟢 360° STREAMING" if lidar_fresh else "LiDAR: 🟡 CONNECTING..."
            cv2.putText(frame, lidar_str, (OUT_W//2 - 120, OUT_H//2 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 229, 255) if lidar_fresh else (255, 214, 0), 2)
            cv2.putText(frame, "BUILDING INITIAL SLAM MAP...", (OUT_W//2 - 130, OUT_H//2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, "Drive the robot to expand map coverage", (OUT_W//2 - 145, OUT_H//2 + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (139, 148, 158), 1)

        ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buf.tobytes() if ret else b''

    w = map_msg.info.width
    h = map_msg.info.height
    res = map_msg.info.resolution
    ox = map_msg.info.origin.position.x
    oy = map_msg.info.origin.position.y

    data = np.array(map_msg.data, dtype=np.int8).reshape((h, w))
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[data == -1] = (14, 18, 26)   # Unknown dark
    img[data == 0] = (30, 42, 60)    # Explored free space
    img[data > 50] = (0, 240, 255)   # Obstacle walls in cyan

    img = cv2.flip(img, 0)

    zoom = 28.0 # Pixels per meter
    scale = (zoom * res)
    scaled_w = max(1, int(w * scale))
    scaled_h = max(1, int(h * scale))
    scaled_map = cv2.resize(img, (scaled_w, scaled_h), interpolation=cv2.INTER_NEAREST)

    canvas = np.zeros((OUT_H, OUT_W, 3), dtype=np.uint8)
    canvas[:] = (10, 14, 23)

    cx = OUT_W // 2
    cy = OUT_H // 2

    sc_rx = int((rx - ox) * zoom)
    sc_ry = scaled_h - int((ry - oy) * zoom)

    top_left_x = cx - sc_rx
    top_left_y = cy - sc_ry

    x1 = max(0, top_left_x)
    y1 = max(0, top_left_y)
    x2 = min(OUT_W, top_left_x + scaled_w)
    y2 = min(OUT_H, top_left_y + scaled_h)

    mx1 = max(0, -top_left_x)
    my1 = max(0, -top_left_y)
    mx2 = mx1 + (x2 - x1)
    my2 = my1 + (y2 - y1)

    if x2 > x1 and y2 > y1 and mx2 > mx1 and my2 > my1:
        canvas[y1:y2, x1:x2] = scaled_map[my1:my2, mx1:mx2]

    # Grid crosshairs
    meter_px = int(zoom)
    for gx in range(cx % meter_px, OUT_W, meter_px):
        cv2.line(canvas, (gx, 0), (gx, OUT_H), (20, 28, 40), 1)
    for gy in range(cy % meter_px, OUT_H, meter_px):
        cv2.line(canvas, (0, gy), (OUT_W, gy), (20, 28, 40), 1)

    # Robot Center Marker & Needle
    cv2.circle(canvas, (cx, cy), 10, (255, 215, 0), 2)
    cv2.circle(canvas, (cx, cy), 5, (0, 68, 255), -1)

    rad = math.radians(ryaw)
    tip_x = int(cx + 22 * math.cos(rad))
    tip_y = int(cy - 22 * math.sin(rad))
    cv2.line(canvas, (cx, cy), (tip_x, tip_y), (0, 229, 255), 3)

    # Ball Marker
    if b_tracked:
        fwd = state.ball_x
        lat = state.ball_y
        bx_px = int(cx + (fwd * math.cos(rad) - lat * math.sin(rad)) * zoom)
        by_px = int(cy - (fwd * math.sin(rad) + lat * math.cos(rad)) * zoom)
        if 0 <= bx_px < OUT_W and 0 <= by_px < OUT_H:
            cv2.circle(canvas, (bx_px, by_px), 8, (0, 255, 0), -1)
            cv2.putText(canvas, "BALL", (bx_px + 10, by_px + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    # Overlays
    map_text = f"MAP: {w*res:.1f}m x {h*res:.1f}m"
    cv2.putText(canvas, map_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 229, 255), 1)
    pose_text = f"X:{rx:+.2f}m Y:{ry:+.2f}m θ:{ryaw:+.1f}°"
    cv2.putText(canvas, pose_text, (10, OUT_H - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)

    ret, buf = cv2.imencode('.jpg', canvas, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buf.tobytes() if ret else b''

# ====================================================================
# WEB APP HTML / CSS / JAVASCRIPT (Optimized for Mobile Screens)
# ====================================================================
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>⚽ Soccer Bot Mobile HQ</title>
  <style>
    * {
      box-sizing: border-box;
      -webkit-touch-callout: none;
      -webkit-user-select: none;
      user-select: none;
      margin: 0;
      padding: 0;
    }
    body {
      background: #0d0f14;
      color: #e0e0e0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      overflow-x: hidden;
      padding: 8px;
    }
    header {
      width: 100%;
      max-width: 480px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: #141720;
      border-radius: 12px;
      border: 1px solid #232936;
      margin-bottom: 6px;
    }
    .title {
      font-size: 15px;
      font-weight: 700;
      color: #00e5ff;
      letter-spacing: 0.5px;
    }
    .badge {
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 20px;
      background: #1e3a2f;
      color: #00e676;
      border: 1px solid #00e676;
    }
    .badge.offline {
      background: #3a1e1e;
      color: #ff5252;
      border-color: #ff5252;
    }

    /* View Switcher Tabs */
    .view-switcher {
      display: flex;
      width: 100%;
      max-width: 480px;
      gap: 6px;
      margin-bottom: 6px;
    }
    .view-btn {
      flex: 1;
      padding: 10px;
      font-size: 13px;
      font-weight: 700;
      border-radius: 10px;
      border: 1px solid #232936;
      background: #141720;
      color: #8b949e;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .view-btn.active {
      background: #00e5ff18;
      color: #00e5ff;
      border-color: #00e5ff;
      box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
    }

    /* Stream Containers */
    .streams-wrapper {
      width: 100%;
      max-width: 480px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 6px;
    }
    .stream-card {
      width: 100%;
      background: #141720;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #232936;
      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
      display: flex;
      flex-direction: column;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 5px 10px;
      background: #181d28;
      border-bottom: 1px solid #232936;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #8b949e;
    }
    .card-header span:first-child {
      display: flex;
      align-items: center;
      gap: 5px;
      color: #00e5ff;
    }
    .mini-badge {
      font-size: 10px;
      padding: 2px 7px;
      border-radius: 12px;
      font-weight: 600;
      font-family: monospace;
    }
    .badge-searching { background: #332612; color: #ffd600; border: 1px solid rgba(255, 214, 0, 0.4); }
    .badge-tracked { background: #12331c; color: #00e676; border: 1px solid rgba(0, 230, 118, 0.4); }
    .badge-active { background: #0e2b38; color: #00e5ff; border: 1px solid rgba(0, 229, 255, 0.4); }
    .badge-scanning { background: #2b2310; color: #ffd600; border: 1px solid rgba(255, 214, 0, 0.4); }

    .media-box {
      position: relative;
      background: #000;
      width: 100%;
      overflow: hidden;
    }
    .stream-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .stream-overlay {
      position: absolute;
      bottom: 6px;
      left: 6px;
      right: 6px;
      display: flex;
      justify-content: space-between;
      pointer-events: none;
    }
    .telemetry-pill {
      background: rgba(14, 18, 26, 0.85);
      backdrop-filter: blur(4px);
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .pill-green { color: #00e676; border-color: rgba(0, 230, 118, 0.3); }
    .pill-cyan { color: #00e5ff; border-color: rgba(0, 229, 255, 0.3); }
    .pill-yellow { color: #ffd600; border-color: rgba(255, 214, 0, 0.3); }

    /* Layout modes */
    .mode-dual .media-box { height: 160px; }
    .mode-cam #mapCard { display: none; }
    .mode-cam .media-box { height: 230px; }
    .mode-map #camCard { display: none; }
    .mode-map .media-box { height: 240px; }

    /* Autopilot Control Card */
    .autopilot-card {
      width: 100%;
      max-width: 480px;
      background: #141720;
      border-radius: 12px;
      padding: 8px;
      border: 1px solid #232936;
      margin-bottom: 6px;
      text-align: center;
    }
    .btn-autopilot {
      width: 100%;
      padding: 12px;
      font-size: 13px;
      font-weight: 700;
      border-radius: 10px;
      border: none;
      background: linear-gradient(135deg, #1b5e20, #2e7d32);
      color: #fff;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(46, 125, 50, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s;
    }
    .btn-autopilot.active {
      background: linear-gradient(135deg, #b71c1c, #d32f2f);
      box-shadow: 0 4px 12px rgba(211, 47, 47, 0.5);
    }
    .status-text {
      font-size: 11px;
      color: #8b949e;
      margin-top: 5px;
      font-family: monospace;
    }

    /* Speed Pills Bar */
    .speed-bar {
      width: 100%;
      max-width: 480px;
      display: flex;
      gap: 6px;
      margin-bottom: 8px;
    }
    .speed-pill {
      flex: 1;
      padding: 8px 4px;
      text-align: center;
      background: #141720;
      border: 1px solid #232936;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 700;
      color: #8b949e;
      cursor: pointer;
      transition: all 0.2s;
    }
    .speed-pill.active {
      background: #00e5ff;
      color: #000;
      border-color: #00e5ff;
      box-shadow: 0 0 10px rgba(0, 229, 255, 0.4);
    }

    /* Touch D-Pad */
    .controls-container {
      width: 100%;
      max-width: 480px;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 6px 0;
    }
    .dpad-grid {
      display: grid;
      grid-template-columns: repeat(3, 76px);
      grid-template-rows: repeat(3, 76px);
      gap: 8px;
    }
    .dpad-btn {
      background: #181d28;
      border: 2px solid #2a3346;
      border-radius: 16px;
      color: #fff;
      font-size: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 4px 10px rgba(0,0,0,0.4);
      transition: all 0.1s ease;
      touch-action: manipulation;
    }
    .dpad-btn:active, .dpad-btn.pressed {
      background: #00e5ff;
      color: #000;
      border-color: #00e5ff;
      transform: scale(0.94);
      box-shadow: 0 0 16px rgba(0, 229, 255, 0.6);
    }
    .dpad-stop {
      background: #2a1b1b;
      border-color: #552525;
      color: #ff5252;
      font-size: 13px;
      font-weight: 800;
    }
    .dpad-stop:active, .dpad-stop.pressed {
      background: #ff5252;
      color: #fff;
      border-color: #ff5252;
      box-shadow: 0 0 16px rgba(255, 82, 82, 0.6);
    }

    /* Robotic Arm Card */
    .arm-card {
      width: 100%;
      max-width: 480px;
      background: #141720;
      border-radius: 12px;
      padding: 10px;
      border: 1px solid #232936;
      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
      margin-top: 8px;
      margin-bottom: 12px;
    }
    .arm-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 8px;
      border-bottom: 1px solid #232936;
      font-size: 12px;
      font-weight: 700;
      color: #00e5ff;
    }
    .arm-presets-bar {
      display: flex;
      gap: 6px;
      margin: 8px 0;
      overflow-x: auto;
    }
    .arm-preset-btn {
      flex: 1;
      padding: 8px 4px;
      background: #1c2230;
      border: 1px solid #2a3346;
      border-radius: 8px;
      color: #e0e0e0;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }
    .arm-preset-btn:active {
      transform: scale(0.95);
      border-color: #00e5ff;
    }
    .btn-grab {
      background: #2a1b1b;
      border-color: #552525;
      color: #ff5252;
    }
    .btn-open {
      background: #12331c;
      border-color: #1e5c2e;
      color: #00e676;
    }
    .btn-test {
      background: #292414;
      border-color: #55441a;
      color: #ffd600;
    }
    .arm-joints {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-top: 6px;
    }
    .joint-row {
      display: flex;
      flex-direction: column;
      gap: 2px;
      background: #0f121a;
      padding: 6px 8px;
      border-radius: 8px;
      border: 1px solid #1f2533;
    }
    .joint-info {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      font-weight: 600;
      color: #8b949e;
    }
    .joint-val {
      font-family: monospace;
      color: #00e5ff;
      font-weight: 700;
    }
    .joint-slider-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 4px;
    }
    .jog-btn {
      width: 28px;
      height: 28px;
      background: #1c2230;
      border: 1px solid #2a3346;
      border-radius: 6px;
      color: #fff;
      font-size: 14px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      touch-action: manipulation;
    }
    .jog-btn:active {
      background: #00e5ff;
      color: #000;
    }
    .arm-slider {
      flex: 1;
      height: 6px;
      border-radius: 3px;
      background: #232936;
      outline: none;
      -webkit-appearance: none;
    }
    .arm-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #00e5ff;
      cursor: pointer;
      box-shadow: 0 0 6px rgba(0, 229, 255, 0.6);
    }
    .quick-angles {
      display: flex;
      gap: 6px;
      margin-top: 6px;
      flex-wrap: wrap;
    }
    .angle-btn {
      padding: 5px 9px;
      background: #181d27;
      border: 1px solid #2a3346;
      border-radius: 6px;
      color: #00e5ff;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
      white-space: nowrap;
    }
    .angle-btn:active {
      background: #00e5ff;
      color: #000;
      transform: scale(0.95);
    }
    .btn-sweep {
      background: #292414 !important;
      border-color: #55441a !important;
      color: #ffd600 !important;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <header>
    <div class="title">⚽ SOCCER BOT HQ</div>
    <div id="connBadge" class="badge">● CONNECTING...</div>
  </header>

  <!-- View Switcher -->
  <div class="view-switcher">
    <button id="viewDualBtn" class="view-btn active" onclick="switchView('dual')">✨ Dual View</button>
    <button id="viewCamBtn" class="view-btn" onclick="switchView('cam')">📷 Camera</button>
    <button id="viewMapBtn" class="view-btn" onclick="switchView('map')">🗺️ LiDAR Map</button>
  </div>

  <!-- Streams Container -->
  <div id="streamsWrapper" class="streams-wrapper mode-dual">
    <!-- Camera Feed Card -->
    <div id="camCard" class="stream-card">
      <div class="card-header">
        <span>📷 LIVE CAMERA FEED</span>
        <span id="ballBadge" class="mini-badge badge-searching">⚽ SEARCHING...</span>
      </div>
      <div class="media-box">
        <img id="camImg" class="stream-img" src="/stream.mjpg" alt="Camera Feed">
      </div>
    </div>

    <!-- 2D LiDAR SLAM Map Card -->
    <div id="mapCard" class="stream-card">
      <div class="card-header">
        <span>🗺️ 2D LIDAR SLAM MAP</span>
        <span id="lidarBadge" class="mini-badge badge-active">📡 360° ACTIVE</span>
      </div>
      <div class="media-box">
        <img id="mapImg" class="stream-img" src="/map_stream.mjpg" alt="2D SLAM Map">
        <div class="stream-overlay">
          <div id="poseTelemetry" class="telemetry-pill pill-cyan">θ: +0.0° | X: +0.00m Y: +0.00m</div>
          <div id="slamBadge" class="telemetry-pill pill-green">SLAM: ONLINE</div>
        </div>
      </div>
    </div>
  </div>

  <!-- 4-SERVO ROBOTIC ARM CONTROLLER -->
  <div class="arm-card">
    <div class="arm-card-header">
      <span>🦾 4-SERVO ROBOTIC ARM CONTROLLER</span>
      <span id="armConnBadge" class="mini-badge badge-active">LINKED (9001)</span>
    </div>

    <!-- Quick Action Presets -->
    <div class="arm-presets-bar">
      <button class="arm-preset-btn" onclick="sendArmPreset('home')">🏠 Home</button>
      <button class="arm-preset-btn" onclick="sendArmPreset('ready')">🎯 Ready</button>
      <button class="arm-preset-btn btn-grab" onclick="sendArmPreset('grab')">✊ Clamp</button>
      <button class="arm-preset-btn btn-open" onclick="sendArmPreset('open')">✋ Open</button>
      <button class="arm-preset-btn btn-test" onclick="testBaseSweep()">⚡ Base Sweep Test</button>
    </div>

    <!-- Joint Controls -->
    <div class="arm-joints">
      <!-- Base Joint -->
      <div class="joint-row">
        <div class="joint-info">
          <span class="joint-label">🔷 BASE SERVO (Arduino Pin 9)</span>
          <span id="valBase" class="joint-val">0°</span>
        </div>
        <div class="joint-slider-wrap">
          <button class="jog-btn" onclick="jogJoint('B', -5)">-</button>
          <input type="range" id="sliderBase" min="0" max="180" value="0" class="arm-slider" oninput="updateJointLabel('B', this.value)" onchange="onJointChange('B', this.value)">
          <button class="jog-btn" onclick="jogJoint('B', +5)">+</button>
        </div>
        <div class="quick-angles">
          <button class="angle-btn" onclick="sendAngle('B', 0)">0° Left</button>
          <button class="angle-btn" onclick="sendAngle('B', 45)">45°</button>
          <button class="angle-btn" onclick="sendAngle('B', 90)">90° Center</button>
          <button class="angle-btn" onclick="sendAngle('B', 135)">135°</button>
          <button class="angle-btn" onclick="sendAngle('B', 180)">180° Right</button>
          <button class="angle-btn btn-sweep" onclick="testBaseSweep()">⚡ Test Sweep</button>
        </div>
      </div>

      <!-- Shoulder Joint -->
      <div class="joint-row">
        <div class="joint-info">
          <span class="joint-label">🔷 SHOULDER SERVO (Arduino Pin 10)</span>
          <span id="valShoulder" class="joint-val">0°</span>
        </div>
        <div class="joint-slider-wrap">
          <button class="jog-btn" onclick="jogJoint('S', -5)">-</button>
          <input type="range" id="sliderShoulder" min="0" max="180" value="0" class="arm-slider" oninput="updateJointLabel('S', this.value)" onchange="onJointChange('S', this.value)">
          <button class="jog-btn" onclick="jogJoint('S', +5)">+</button>
        </div>
        <div class="quick-angles">
          <button class="angle-btn" onclick="sendAngle('S', 0)">0° Flat</button>
          <button class="angle-btn" onclick="sendAngle('S', 30)">30° Low</button>
          <button class="angle-btn" onclick="sendAngle('S', 60)">60° Mid</button>
          <button class="angle-btn" onclick="sendAngle('S', 90)">90° Up</button>
        </div>
      </div>

      <!-- Elbow / Albo Joint -->
      <div class="joint-row">
        <div class="joint-info">
          <span class="joint-label">🔷 ELBOW / ALBO SERVO (Arduino Pin 11)</span>
          <span id="valAlbo" class="joint-val">0°</span>
        </div>
        <div class="joint-slider-wrap">
          <button class="jog-btn" onclick="jogJoint('A', -5)">-</button>
          <input type="range" id="sliderAlbo" min="0" max="180" value="0" class="arm-slider" oninput="updateJointLabel('A', this.value)" onchange="onJointChange('A', this.value)">
          <button class="jog-btn" onclick="jogJoint('A', +5)">+</button>
        </div>
        <div class="quick-angles">
          <button class="angle-btn" onclick="sendAngle('A', 0)">0° Fold</button>
          <button class="angle-btn" onclick="sendAngle('A', 30)">30° Reach</button>
          <button class="angle-btn" onclick="sendAngle('A', 60)">60° Extend</button>
          <button class="angle-btn" onclick="sendAngle('A', 90)">90° Up</button>
        </div>
      </div>

      <!-- Gripper Joint -->
      <div class="joint-row">
        <div class="joint-info">
          <span class="joint-label">🔷 GRIPPER CLAW (Arduino Pin 12)</span>
          <span id="valGripper" class="joint-val">180° (Neutral)</span>
        </div>
        <div class="joint-slider-wrap">
          <button class="jog-btn" onclick="jogJoint('G', -10)">-</button>
          <input type="range" id="sliderGripper" min="115" max="270" value="180" class="arm-slider" oninput="updateJointLabel('G', this.value)" onchange="onJointChange('G', this.value)">
          <button class="jog-btn" onclick="jogJoint('G', +10)">+</button>
        </div>
        <div class="quick-angles">
          <button class="angle-btn btn-grab" onclick="sendAngle('G', 125)">✊ Clamp (125°)</button>
          <button class="angle-btn" onclick="sendAngle('G', 180)">✋ Neutral (180°)</button>
          <button class="angle-btn btn-open" onclick="sendAngle('G', 240)">👐 Open (240°)</button>
        </div>
      </div>
    </div>
    <div id="armStatusText" class="status-text">Status: Ready | Safe Neutral: B:0 S:0 A:0 G:180</div>
  </div>

  <!-- Touch D-Pad -->
  <div class="controls-container">
    <div class="dpad-grid">
      <div></div>
      <button class="dpad-btn" data-action="F">▲</button>
      <div></div>
      
      <button class="dpad-btn" data-action="L">◀</button>
      <button class="dpad-btn dpad-stop" data-action="S">STOP</button>
      <button class="dpad-btn" data-action="R">▶</button>
      
      <div></div>
      <button class="dpad-btn" data-action="B">▼</button>
      <div></div>
    </div>
  </div>

  <!-- Speed Selector -->
  <div class="speed-bar">
    <div class="speed-pill" onclick="setSpeed(85, this)">SLOW (85)</div>
    <div class="speed-pill active" onclick="setSpeed(120, this)">CRUISE (120)</div>
    <div class="speed-pill" onclick="setSpeed(160, this)">FAST (160)</div>
    <div class="speed-pill" onclick="setSpeed(210, this)">SPORT (210)</div>
  </div>

  <!-- Autopilot Card -->
  <div class="autopilot-card">
    <button id="autopilotBtn" class="btn-autopilot" onclick="toggleAutopilot()">
      <span>⚽</span> <span>START BALL AUTOPILOT</span>
    </button>
    <div id="autopilotStatus" class="status-text">IDLE (Manual Mode)</div>
  </div>

  <script>
    let currentSpeed = 120;
    let autopilotActive = false;
    let activePressInterval = null;
    let currentView = 'dual';

    function switchView(mode) {
      currentView = mode;
      document.getElementById('viewDualBtn').className = (mode === 'dual') ? 'view-btn active' : 'view-btn';
      document.getElementById('viewCamBtn').className = (mode === 'cam') ? 'view-btn active' : 'view-btn';
      document.getElementById('viewMapBtn').className = (mode === 'map') ? 'view-btn active' : 'view-btn';
      const wrapper = document.getElementById('streamsWrapper');
      wrapper.className = 'streams-wrapper mode-' + mode;
    }

    function setSpeed(spd, el) {
      currentSpeed = spd;
      document.querySelectorAll('.speed-pill').forEach(p => p.classList.remove('active'));
      el.classList.add('active');
      fetch('/api/speed', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({speed: spd})
      });
    }

    function toggleAutopilot() {
      autopilotActive = !autopilotActive;
      const btn = document.getElementById('autopilotBtn');
      if (autopilotActive) {
        btn.classList.add('active');
        btn.innerHTML = '<span>⏹️</span> <span>STOP AUTOPILOT</span>';
      } else {
        btn.classList.remove('active');
        btn.innerHTML = '<span>⚽</span> <span>START BALL AUTOPILOT</span>';
      }
      fetch('/api/autopilot', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({active: autopilotActive})
      });
    }

    function sendDrive(action) {
      if (autopilotActive && action !== 'S') {
        autopilotActive = false;
        const btn = document.getElementById('autopilotBtn');
        btn.classList.remove('active');
        btn.innerHTML = '<span>⚽</span> <span>START BALL AUTOPILOT</span>';
      }
      fetch('/api/drive', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: action, speed: currentSpeed})
      });
    }

    // Touch & Mouse Handlers for Smooth Driving
    document.querySelectorAll('.dpad-btn').forEach(btn => {
      const act = btn.getAttribute('data-action');
      
      const startAction = (e) => {
        e.preventDefault();
        btn.classList.add('pressed');
        sendDrive(act);
        if (act !== 'S') {
          clearInterval(activePressInterval);
          activePressInterval = setInterval(() => sendDrive(act), 200);
        }
      };

      const stopAction = (e) => {
        e.preventDefault();
        btn.classList.remove('pressed');
        clearInterval(activePressInterval);
        if (act !== 'S') {
          sendDrive('S');
        }
      };

      btn.addEventListener('touchstart', startAction, {passive: false});
      btn.addEventListener('touchend', stopAction, {passive: false});
      btn.addEventListener('touchcancel', stopAction, {passive: false});
      btn.addEventListener('mousedown', startAction);
      btn.addEventListener('mouseup', stopAction);
      btn.addEventListener('mouseleave', stopAction);
    });

    // Keyboard Fallback (W, A, S, D, Arrows, Space)
    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      const k = e.key.toLowerCase();
      if (k === 'w' || k === 'arrowup') sendDrive('F');
      else if (k === 's' || k === 'arrowdown') sendDrive('B');
      else if (k === 'a' || k === 'arrowleft') sendDrive('L');
      else if (k === 'd' || k === 'arrowright') sendDrive('R');
      else if (k === ' ' || k === 'x') sendDrive('S');
    });

    window.addEventListener('keyup', (e) => {
      const k = e.key.toLowerCase();
      if (['w', 's', 'a', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) {
        sendDrive('S');
      }
    });

    // Telemetry Poller (Updates HUD every 250ms)
    setInterval(() => {
      fetch('/api/status')
        .then(r => r.json())
        .then(data => {
          const conn = document.getElementById('connBadge');
          if (data.connected) {
            conn.className = 'badge';
            conn.innerText = '● ONLINE';
          } else {
            conn.className = 'badge offline';
            conn.innerText = '● OFFLINE';
          }

          // Ball Telemetry
          const ball = document.getElementById('ballBadge');
          if (ball) {
            if (data.ball_tracked) {
              ball.className = 'mini-badge badge-tracked';
              ball.innerText = `⚽ ${data.dist.toFixed(2)}m (${data.bearing > 0 ? '+' : ''}${data.bearing.toFixed(1)}°)`;
            } else {
              ball.className = 'mini-badge badge-searching';
              ball.innerText = '⚽ SEARCHING...';
            }
          }

          // LiDAR Telemetry
          const ldr = document.getElementById('lidarBadge');
          if (ldr) {
            if (data.lidar_active) {
              ldr.className = 'mini-badge badge-active';
              ldr.innerText = `📡 360° ACTIVE`;
            } else {
              ldr.className = 'mini-badge badge-scanning';
              ldr.innerText = '📡 SCANNING...';
            }
          }

          // Pose Telemetry
          const poseEl = document.getElementById('poseTelemetry');
          if (poseEl) {
            const rx = (typeof data.robot_x === 'number') ? data.robot_x : 0;
            const ry = (typeof data.robot_y === 'number') ? data.robot_y : 0;
            const ryaw = (typeof data.robot_yaw === 'number') ? data.robot_yaw : 0;
            poseEl.innerText = `θ: ${ryaw > 0 ? '+' : ''}${ryaw.toFixed(1)}° | X: ${rx > 0 ? '+' : ''}${rx.toFixed(2)}m Y: ${ry > 0 ? '+' : ''}${ry.toFixed(2)}m`;
          }

          // Autopilot Status
          document.getElementById('autopilotStatus').innerText = data.autopilot_status;

          // Robotic Arm Telemetry
          if (data.arm_base !== undefined) {
            updateArmUI(data);
          }
        })
        .catch(() => {});
    }, 250);

    // ====================================================
    // ROBOTIC ARM JAVASCRIPT CONTROLLERS
    // ====================================================
    let armDragging = false;
    let armDebounceTimer = null;

    function sendArmPreset(preset) {
      const st = document.getElementById('armStatusText');
      if (st) st.innerText = `Status: Executing ${preset.toUpperCase()}...`;
      fetch('/api/arm', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: preset})
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'OK') {
          updateArmUI(data);
          if (st) st.innerText = `Status: ${data.response || 'OK'}`;
        } else {
          if (st) st.innerText = `Status: Error - ${data.msg || 'Failed'}`;
        }
      })
      .catch(err => {
        if (st) st.innerText = `Status: Network Error`;
      });
    }

    function onJointInput(joint, val) {
      armDragging = true;
      updateJointLabel(joint, val);
    }

    function onJointChange(joint, val) {
      armDragging = false;
      sendJointCmd(joint, val);
    }

    function sendAngle(joint, angle) {
      let sliderId = (joint === 'B') ? 'sliderBase' : (joint === 'S') ? 'sliderShoulder' : (joint === 'A') ? 'sliderAlbo' : 'sliderGripper';
      let slider = document.getElementById(sliderId);
      if (slider) slider.value = angle;
      updateJointLabel(joint, angle);
      sendJointCmd(joint, angle);
    }

    function testBaseSweep() {
      const st = document.getElementById('armStatusText');
      if (st) st.innerText = 'Status: 🔄 Running Base Sweep Test (0° -> 135° -> 0°)...';
      fetch('/api/arm/test_base', {method: 'POST'})
        .then(res => res.json())
        .then(data => {
          if (st) st.innerText = 'Status: Base sweep test in progress...';
        })
        .catch(() => {
          if (st) st.innerText = 'Status: Sweep test request failed';
        });
    }

    function jogJoint(joint, delta) {
      let sliderId = (joint === 'B') ? 'sliderBase' : (joint === 'S') ? 'sliderShoulder' : (joint === 'A') ? 'sliderAlbo' : 'sliderGripper';
      let slider = document.getElementById(sliderId);
      if (!slider) return;
      let newVal = Math.max(parseInt(slider.min), Math.min(parseInt(slider.max), parseInt(slider.value) + delta));
      slider.value = newVal;
      updateJointLabel(joint, newVal);
      sendJointCmd(joint, newVal);
    }

    function sendJointCmd(joint, angle) {
      const st = document.getElementById('armStatusText');
      if (st) st.innerText = `Status: Moving joint ${joint} to ${angle}°...`;
      fetch('/api/arm', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: 'joint', joint: joint, angle: parseInt(angle)})
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'OK') {
          updateArmUI(data);
          if (st) st.innerText = `Status: OK | Joint ${joint} at ${angle}°`;
        } else {
          if (st) st.innerText = `Status: Error - ${data.msg || 'Failed'}`;
        }
      })
      .catch(() => {
        if (st) st.innerText = `Status: Network Error`;
      });
    }

    function updateJointLabel(joint, val) {
      val = parseInt(val);
      if (joint === 'B') document.getElementById('valBase').innerText = val + '°';
      else if (joint === 'S') document.getElementById('valShoulder').innerText = val + '°';
      else if (joint === 'A') document.getElementById('valAlbo').innerText = val + '°';
      else if (joint === 'G') document.getElementById('valGripper').innerText = val + '° ' + (val <= 130 ? '(Grip)' : val >= 220 ? '(Open)' : '(Neutral)');
    }

    function updateArmUI(data) {
      if (!armDragging) {
        if (data.arm_base !== undefined || data.base !== undefined) {
          const b = data.base !== undefined ? data.base : data.arm_base;
          const s = data.shoulder !== undefined ? data.shoulder : data.arm_shoulder;
          const a = data.albo !== undefined ? data.albo : data.arm_albo;
          const g = data.gripper !== undefined ? data.gripper : data.arm_gripper;

          const sb = document.getElementById('sliderBase');
          const ss = document.getElementById('sliderShoulder');
          const sa = document.getElementById('sliderAlbo');
          const sg = document.getElementById('sliderGripper');

          if (sb && sb.value != b) { sb.value = b; updateJointLabel('B', b); }
          if (ss && ss.value != s) { ss.value = s; updateJointLabel('S', s); }
          if (sa && sa.value != a) { sa.value = a; updateJointLabel('A', a); }
          if (sg && sg.value != g) { sg.value = g; updateJointLabel('G', g); }
        }
      }
      const badge = document.getElementById('armConnBadge');
      if (badge) {
        const isConn = data.arm_connected !== undefined ? data.arm_connected : data.connected;
        if (isConn) {
          badge.className = 'mini-badge badge-active';
          badge.innerText = 'LINKED (9001)';
        } else {
          badge.className = 'mini-badge badge-searching';
          badge.innerText = 'OFFLINE';
        }
      }
    }
  </script>
</body>
</html>
"""

# ====================================================================
# HTTP REQUEST HANDLER
# ====================================================================
class TeleopHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--frame')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()
            try:
                while True:
                    frame_bytes = get_current_camera_frame()
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(frame_bytes)}\r\n\r\n".encode())
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b"\r\n")
                    time.sleep(0.04)
            except Exception:
                pass
        elif self.path == '/map_stream.mjpg':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--frame')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()
            try:
                while True:
                    frame_bytes = render_slam_map_frame()
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(frame_bytes)}\r\n\r\n".encode())
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b"\r\n")
                    time.sleep(0.08)
            except Exception:
                pass
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with state.lock:
                now = time.time()
                tracked = (now - state.ball_time) < 1.2 and state.ball_dist > 0
                dist = state.ball_dist if tracked else 0.0
                fwd = max(0.01, state.ball_x)
                bearing = math.degrees(math.atan2(state.ball_y, fwd)) if tracked else 0.0
                resp = {
                    "connected": state.wifi_connected,
                    "current_action": state.current_action,
                    "ball_tracked": tracked,
                    "dist": float(dist),
                    "bearing": float(bearing),
                    "autopilot_active": state.autopilot_active,
                    "autopilot_status": state.autopilot_status,
                    "speed": state.speed,
                    "lidar_active": (now - state.laser_time) < 2.0,
                    "slam_active": state.raw_map is not None,
                    "robot_x": float(state.robot_x),
                    "robot_y": float(state.robot_y),
                    "robot_yaw": float(state.robot_yaw),
                    "arm_connected": state.arm_connected,
                    "arm_base": state.arm_base,
                    "arm_shoulder": state.arm_shoulder,
                    "arm_albo": state.arm_albo,
                    "arm_gripper": state.arm_gripper,
                    "arm_status": state.arm_status_msg
                }
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b'{}'
        try:
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}

        if self.path == '/api/drive':
            act = data.get('action', 'S')
            spd = data.get('speed', state.speed)
            send_motor_command(act, spd)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        elif self.path == '/api/autopilot':
            active = bool(data.get('active', False))
            with state.lock:
                state.autopilot_active = active
                if not active:
                    state.autopilot_status = "IDLE (Manual Mode)"
            if not active:
                send_motor_command('S')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        elif self.path == '/api/speed':
            spd = int(data.get('speed', 120))
            with state.lock:
                state.speed = spd
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        elif self.path == '/api/arm':
            res = send_arm_command(data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif self.path == '/api/arm/test_base':
            run_base_sweep_test()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status":"ok","msg":"Base sweep test started"}')
        else:
            self.send_response(404)
            self.end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def main():
    server = ThreadedHTTPServer(('0.0.0.0', WEB_PORT), TeleopHandler)
    local_ip = "localhost"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('192.168.0.1', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"

    print("=" * 65)
    print("   [+] SOCCER BOT MOBILE WEB TELEOP & AUTOPILOT ACTIVE")
    print(f"   Open in Laptop Browser: http://localhost:{WEB_PORT}")
    print(f"   Open on Phone Browser:  http://{local_ip}:{WEB_PORT}")
    print(f"   Connected to Robot Pi:  {PI_IP}")
    print("=" * 65, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        send_motor_command('S')
        server.server_close()

if __name__ == '__main__':
    main()
