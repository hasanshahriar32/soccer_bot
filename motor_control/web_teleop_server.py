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

PI_IP = "192.168.0.135"
PI_MOTOR_PORT = 9000
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
        self.raw_map = None
        self.map_time = 0.0
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0

state = RobotState()

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

# Direct HTTP Camera Stream Worker (Pulls from Pi port 8000 when ROS 2 topic is idle)
def http_camera_worker():
    import urllib.request
    stream_url = f"http://{PI_IP}:8000/video"
    while True:
        try:
            req = urllib.request.Request(stream_url)
            stream = urllib.request.urlopen(req, timeout=5)
            bytes_buf = b''
            while True:
                with state.lock:
                    ros2_fresh = (time.time() - state.last_frame_time) < 0.5
                if ros2_fresh:
                    time.sleep(0.3)
                    continue

                chunk = stream.read(4096)
                if not chunk:
                    break
                bytes_buf += chunk
                a = bytes_buf.find(b'\xff\xd8')
                b = bytes_buf.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_buf[a:b+2]
                    bytes_buf = bytes_buf[b+2:]
                    with state.lock:
                        state.latest_jpeg = jpg
                        state.last_frame_time = time.time()
        except Exception:
            time.sleep(2.0)

threading.Thread(target=http_camera_worker, daemon=True).start()

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
        rx = state.robot_x
        ry = state.robot_y
        ryaw = state.robot_yaw
        bx = state.ball_x
        by = state.ball_y
        b_tracked = state.ball_tracked
        lidar_fresh = (time.time() - state.laser_time) < 2.0

    OUT_W, OUT_H = 480, 240
    if map_msg is None:
        frame = np.zeros((OUT_H, OUT_W, 3), dtype=np.uint8)
        frame[:] = (10, 14, 23)
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

    /* Stream Container */
    .stream-card {
      width: 100%;
      max-width: 480px;
      background: #000;
      border-radius: 14px;
      overflow: hidden;
      border: 2px solid #232936;
      position: relative;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      margin-bottom: 6px;
    }
    .stream-img {
      width: 100%;
      height: 220px;
      object-fit: cover;
      display: block;
    }
    .stream-overlay {
      position: absolute;
      top: 8px;
      left: 8px;
      right: 8px;
      display: flex;
      justify-content: space-between;
      pointer-events: none;
    }
    .telemetry-pill {
      background: rgba(14, 18, 26, 0.85);
      backdrop-filter: blur(4px);
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 600;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .pill-green { color: #00e676; border-color: rgba(0, 230, 118, 0.3); }
    .pill-cyan { color: #00e5ff; border-color: rgba(0, 229, 255, 0.3); }
    .pill-yellow { color: #ffd600; border-color: rgba(255, 214, 0, 0.3); }

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
  </style>
</head>
<body>
  <header>
    <div class="title">⚽ SOCCER BOT HQ</div>
    <div id="connBadge" class="badge">● CONNECTING...</div>
  </header>

  <!-- View Switcher -->
  <div class="view-switcher">
    <button id="viewCamBtn" class="view-btn active" onclick="switchView('cam')">📷 Camera Feed</button>
    <button id="viewMapBtn" class="view-btn" onclick="switchView('map')">🗺️ 2D LiDAR SLAM Map</button>
  </div>

  <!-- Video Stream / SLAM Map Card -->
  <div class="stream-card">
    <img id="streamImg" class="stream-img" src="/stream.mjpg" alt="Robot Feed">
    <div class="stream-overlay">
      <div id="ballTelemetry" class="telemetry-pill pill-yellow">⚽ SEARCHING...</div>
      <div id="lidarTelemetry" class="telemetry-pill pill-cyan">📡 LiDAR: READY</div>
    </div>
  </div>

  <!-- Autopilot Card -->
  <div class="autopilot-card">
    <button id="autopilotBtn" class="btn-autopilot" onclick="toggleAutopilot()">
      <span>⚽</span> <span>START BALL AUTOPILOT</span>
    </button>
    <div id="autopilotStatus" class="status-text">IDLE (Manual Mode)</div>
  </div>

  <!-- Speed Selector -->
  <div class="speed-bar">
    <div class="speed-pill" onclick="setSpeed(85, this)">SLOW (85)</div>
    <div class="speed-pill active" onclick="setSpeed(120, this)">CRUISE (120)</div>
    <div class="speed-pill" onclick="setSpeed(160, this)">FAST (160)</div>
    <div class="speed-pill" onclick="setSpeed(210, this)">SPORT (210)</div>
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

  <script>
    let currentSpeed = 120;
    let autopilotActive = false;
    let activePressInterval = null;
    let currentView = 'cam';

    function switchView(mode) {
      currentView = mode;
      document.getElementById('viewCamBtn').className = (mode === 'cam') ? 'view-btn active' : 'view-btn';
      document.getElementById('viewMapBtn').className = (mode === 'map') ? 'view-btn active' : 'view-btn';
      const img = document.getElementById('streamImg');
      if (mode === 'cam') {
        img.src = '/stream.mjpg';
      } else {
        img.src = '/map_stream.mjpg';
      }
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
          const ball = document.getElementById('ballTelemetry');
          if (data.ball_tracked) {
            ball.className = 'telemetry-pill pill-green';
            ball.innerText = `⚽ ${data.dist.toFixed(2)}m (${data.bearing > 0 ? '+' : ''}${data.bearing.toFixed(1)}°)`;
          } else {
            ball.className = 'telemetry-pill pill-yellow';
            ball.innerText = '⚽ SEARCHING...';
          }

          // LiDAR Telemetry
          const ldr = document.getElementById('lidarTelemetry');
          if (data.lidar_active) {
            ldr.className = 'telemetry-pill pill-cyan';
            ldr.innerText = `📡 LiDAR: 🟢 360° | X:${data.robot_x.toFixed(1)}m`;
          } else {
            ldr.className = 'telemetry-pill pill-yellow';
            ldr.innerText = '📡 LiDAR: SCANNING...';
          }

          // Autopilot Status
          document.getElementById('autopilotStatus').innerText = data.autopilot_status;
        })
        .catch(() => {});
    }, 250);
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
                    "robot_yaw": float(state.robot_yaw)
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
        else:
            self.send_response(404)
            self.end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def main():
    server = ThreadedHTTPServer(('0.0.0.0', WEB_PORT), TeleopHandler)
    print("=" * 65)
    print("   📱 SOCCER BOT MOBILE WEB TELEOP & AUTOPILOT ACTIVE")
    print(f"   Open on your phone browser: http://192.168.0.122:{WEB_PORT}")
    print(f"   Listening on: http://0.0.0.0:{WEB_PORT}")
    print("=" * 65, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        send_motor_command('S')
        server.server_close()

if __name__ == '__main__':
    main()
