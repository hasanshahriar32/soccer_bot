#!/usr/bin/env python3
"""
====================================================================
  SOCCER BOT - MOBILE PHONE WEB TELEOP & AUTOPILOT CONTROLLER
====================================================================
Accessible from any phone browser on the same Wi-Fi:
    http://<LAPTOP_IP>:5050   (e.g., http://192.168.0.122:5050)

Features:
  1. Live Low-Latency Camera Feed (directly above touch controls)
  2. Responsive Touch D-Pad with Hold-to-Drive & Auto-Brake on release
  3. One-Touch Autonomous Ball Follower (Autopilot with LiDAR sync)
  4. Automatic Proximity Stop at 35 cm for Object / Ball Pickup
  5. Live Telemetry HUD: Distance, Bearing, Mode, Status
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
    from sensor_msgs.msg import Image as RosImage
    from geometry_msgs.msg import Point as RosPoint
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

state = RobotState()

# ====================================================================
# MOTOR TCP CLIENT (Communicates with Pi Port 9000)
# ====================================================================
def motor_client_worker():
    while True:
        if state.sock is None:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(2.5)
                s.connect((PI_IP, PI_MOTOR_PORT))
                with state.lock:
                    state.sock = s
                    state.wifi_connected = True
                print(f"[MOTOR CLIENT] Connected to Pi Motor Server at {PI_IP}:{PI_MOTOR_PORT}!", flush=True)
            except Exception:
                with state.lock:
                    state.sock = None
                    state.wifi_connected = False
                time.sleep(2.0)
        else:
            time.sleep(1.0)

threading.Thread(target=motor_client_worker, daemon=True).start()

def send_motor_command(action, speed=None):
    if speed is None:
        speed = state.speed
    
    with state.lock:
        state.current_action = action
        sock = state.sock

    turn_spd = max(85, int(speed * 0.85))
    if action == 'F':
        pkt = f"SET:{speed},{speed}\n"
    elif action == 'B':
        pkt = f"SET:{-speed},{-speed}\n"
    elif action == 'L':
        pkt = f"SET:{-turn_spd},{turn_spd}\n"
    elif action == 'R':
        pkt = f"SET:{turn_spd},{-turn_spd}\n"
    else:
        pkt = "SET:0,0\n"

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
                fwd = state.ball_x

            if tracked:
                # Proximity Threshold: 0.35m (~14 inches) -> STOP FOR PICKUP TASK
                if dist <= 0.35:
                    send_motor_command('S')
                    with state.lock:
                        state.autopilot_status = f"🎯 BALL REACHED ({dist:.2f}m)! STOPPED READY FOR PICKUP"
                else:
                    if lat > 0.12:
                        # Ball to the left -> Steer left
                        send_motor_command('L', speed=100)
                        with state.lock:
                            state.autopilot_status = f"🔄 ALIGNING: Turning Left (Dist: {dist:.2f}m)"
                    elif lat < -0.12:
                        # Ball to the right -> Steer right
                        send_motor_command('R', speed=100)
                        with state.lock:
                            state.autopilot_status = f"🔄 ALIGNING: Turning Right (Dist: {dist:.2f}m)"
                    else:
                        # Ball centered -> Drive forward
                        send_motor_command('F', speed=120)
                        with state.lock:
                            state.autopilot_status = f"🚀 APPROACHING: Driving Forward to Ball ({dist:.2f}m)"
            else:
                send_motor_command('S')
                with state.lock:
                    state.autopilot_status = "🔍 SEARCHING: No Ball In Sight..."
        time.sleep(0.08)

threading.Thread(target=autopilot_loop, daemon=True).start()

# ====================================================================
# ROS 2 SUBSCRIBER THREAD (Camera & Ball Position)
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
                
                # Overlay Crosshair
                cv2.drawMarker(frame, (w // 2, h // 2), (0, 229, 255), cv2.MARKER_CROSS, 20, 1)

                # Overlay Ball Tracking Visuals if tracked
                with state.lock:
                    tracked = (time.time() - state.ball_time) < 1.2 and state.ball_dist > 0
                    dist = state.ball_dist
                    lat = state.ball_y
                    auto = state.autopilot_active
                    status = state.autopilot_status

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

                # Encode JPEG
                ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ret:
                    with state.lock:
                        state.latest_jpeg = buf.tobytes()
                        state.last_frame_time = time.time()
            except Exception as e:
                pass

        def ball_cb(msg: RosPoint):
            with state.lock:
                state.ball_x = msg.x
                state.ball_y = msg.y
                state.ball_dist = msg.z
                state.ball_time = time.time()
                state.ball_tracked = (msg.z > 0)

        node.create_subscription(RosImage, '/image_raw', image_cb, 5)
        node.create_subscription(RosPoint, '/ball_position', ball_cb, 10)

        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
        node.destroy_node()
    except Exception as e:
        print(f"[ROS2 WORKER ERR] {e}", flush=True)

threading.Thread(target=ros2_subscriber_worker, daemon=True).start()

# Generate Synthetic HUD frame if camera not yet streaming
def get_current_frame():
    with state.lock:
        if state.latest_jpeg and (time.time() - state.last_frame_time) < 1.5:
            return state.latest_jpeg
        tracked = state.ball_tracked
        dist = state.ball_dist
        status = state.autopilot_status
        auto = state.autopilot_active

    # Clean Synthetic Radar Frame (320x240)
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    frame[:] = (18, 18, 24) # Dark slate background

    # Radar concentric circles
    cv2.circle(frame, (160, 160), 40, (35, 45, 50), 1)
    cv2.circle(frame, (160, 160), 80, (35, 45, 50), 1)
    cv2.circle(frame, (160, 160), 120, (35, 45, 50), 1)
    cv2.line(frame, (160, 20), (160, 220), (35, 45, 50), 1)
    cv2.line(frame, (20, 160), (300, 160), (35, 45, 50), 1)

    # Robot Center
    cv2.circle(frame, (160, 160), 6, (0, 229, 255), -1)
    cv2.putText(frame, "ROBOT", (145, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 229, 255), 1)

    if tracked and dist > 0:
        cv2.putText(frame, f"BALL: {dist:.2f}m", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 230, 118), 1)
        cv2.circle(frame, (160, 80), 8, (0, 230, 118), -1)
    else:
        cv2.putText(frame, "RADAR ACTIVE / SEARCHING...", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 214, 0), 1)

    cv2.putText(frame, "STANDBY CAMERA FEED", (90, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 100), 1)

    mode_str = "[AUTOPILOT ACTIVE]" if auto else "[MANUAL TELEOP]"
    cv2.putText(frame, mode_str, (10, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 230, 118) if auto else (0, 229, 255), 1)

    ret, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return buf.tobytes() if ret else b''

# ====================================================================
# WEB APP HTML / CSS / JAVASCRIPT (Optimized for Mobile Screens)
# ====================================================================
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
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
      padding: 10px;
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
      margin-bottom: 8px;
    }
    .title {
      font-size: 16px;
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

    /* Video Container */
    .stream-card {
      width: 100%;
      max-width: 480px;
      background: #000;
      border-radius: 14px;
      overflow: hidden;
      border: 2px solid #232936;
      position: relative;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      margin-bottom: 8px;
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
    .pill-yellow { color: #ffd600; border-color: rgba(255, 214, 0, 0.3); }

    /* Autopilot Control Card */
    .autopilot-card {
      width: 100%;
      max-width: 480px;
      background: #141720;
      border-radius: 12px;
      padding: 10px;
      border: 1px solid #232936;
      margin-bottom: 8px;
      text-align: center;
    }
    .btn-autopilot {
      width: 100%;
      padding: 13px;
      font-size: 14px;
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
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.6); }
      70% { box-shadow: 0 0 0 10px rgba(211, 47, 47, 0); }
      100% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }
    }
    .auto-status {
      font-size: 11px;
      margin-top: 6px;
      color: #9e9e9e;
      font-weight: 500;
    }

    /* Speed Selector */
    .speed-bar {
      width: 100%;
      max-width: 480px;
      display: flex;
      gap: 6px;
      margin-bottom: 8px;
    }
    .btn-speed {
      flex: 1;
      padding: 7px 4px;
      background: #141720;
      border: 1px solid #232936;
      color: #9e9e9e;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-speed.selected {
      background: #00e5ff;
      color: #0a0a0f;
      border-color: #00e5ff;
      font-weight: 700;
    }

    /* Touch D-Pad */
    .dpad-container {
      width: 100%;
      max-width: 480px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-template-rows: repeat(3, 72px);
      gap: 8px;
      margin-bottom: 10px;
    }
    .dpad-btn {
      background: #181d28;
      border: 1px solid #283144;
      border-radius: 14px;
      color: #fff;
      font-size: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 2px;
      cursor: pointer;
      box-shadow: 0 3px 8px rgba(0,0,0,0.3);
      touch-action: none;
    }
    .dpad-btn span {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      opacity: 0.8;
    }
    .dpad-btn:active, .dpad-btn.pressed {
      background: #00e5ff;
      color: #0a0a0f;
      transform: scale(0.96);
      box-shadow: 0 0 16px rgba(0, 229, 255, 0.6);
    }
    .btn-fwd { grid-column: 2; grid-row: 1; border-color: #00e676; color: #00e676; }
    .btn-fwd:active, .btn-fwd.pressed { background: #00e676; color: #000; }
    .btn-left { grid-column: 1; grid-row: 2; border-color: #29b6f6; color: #29b6f6; }
    .btn-left:active, .btn-left.pressed { background: #29b6f6; color: #000; }
    .btn-stop { grid-column: 2; grid-row: 2; border-color: #ff5252; color: #ff5252; font-size: 22px; }
    .btn-stop:active, .btn-stop.pressed { background: #ff5252; color: #fff; }
    .btn-right { grid-column: 3; grid-row: 2; border-color: #29b6f6; color: #29b6f6; }
    .btn-right:active, .btn-right.pressed { background: #29b6f6; color: #000; }
    .btn-back { grid-column: 2; grid-row: 3; border-color: #ff9100; color: #ff9100; }
    .btn-back:active, .btn-back.pressed { background: #ff9100; color: #000; }

    footer {
      font-size: 10px;
      color: #616161;
      text-align: center;
      margin-top: auto;
      padding: 6px;
    }
  </style>
</head>
<body>

  <!-- Top Status Bar -->
  <header>
    <div class="title">⚽ SOCCER BOT HQ</div>
    <div id="connBadge" class="badge">● ONLINE</div>
  </header>

  <!-- Live Camera Feed (Directly above controls) -->
  <div class="stream-card">
    <img class="stream-img" src="/stream.mjpg" alt="Live Camera Stream" />
    <div class="stream-overlay">
      <div id="ballTelemetry" class="telemetry-pill pill-yellow">⚽ SEARCHING...</div>
      <div id="actionTelemetry" class="telemetry-pill">STOPPED</div>
    </div>
  </div>

  <!-- Autopilot / Autonomous Ball Follower Card -->
  <div class="autopilot-card">
    <button id="autopilotBtn" class="btn-autopilot" onclick="toggleAutopilot()">
      <span>⚽</span> <span>START BALL AUTOPILOT</span>
    </button>
    <div id="autopilotStatus" class="auto-status">Target: Automatically track & brake at 35cm for pickup.</div>
  </div>

  <!-- Speed Selector Presets -->
  <div class="speed-bar">
    <button class="btn-speed" onclick="setSpeed(85, this)">🐢 Slow</button>
    <button class="btn-speed selected" onclick="setSpeed(120, this)">🚗 Cruise</button>
    <button class="btn-speed" onclick="setSpeed(175, this)">🏎️ Fast</button>
    <button class="btn-speed" onclick="setSpeed(220, this)">⚡ Max</button>
  </div>

  <!-- Touch D-Pad (Touch & Hold to Drive, Release to Stop) -->
  <div class="dpad-container">
    <button class="dpad-btn btn-fwd" data-action="F">▲<span>Forward</span></button>
    <button class="dpad-btn btn-left" data-action="L">◀<span>Left</span></button>
    <button class="dpad-btn btn-stop" data-action="S">⏹<span>STOP</span></button>
    <button class="dpad-btn btn-right" data-action="R">▶<span>Right</span></button>
    <button class="dpad-btn btn-back" data-action="B">▼<span>Back</span></button>
  </div>

  <footer>
    Touch & hold buttons to drive. Release to brake.<br>
    Connected to Pi TCP 9000 & Camera 8000.
  </footer>

  <script>
    let currentSpeed = 120;
    let autopilotActive = false;
    let activePressInterval = null;

    // Set Speed Preset
    function setSpeed(spd, btn) {
      currentSpeed = spd;
      document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      fetch('/api/speed', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({speed: spd})
      });
    }

    // Toggle Autopilot
    function toggleAutopilot() {
      autopilotActive = !autopilotActive;
      const btn = document.getElementById('autopilotBtn');
      if (autopilotActive) {
        btn.classList.add('active');
        btn.innerHTML = '<span>⏹</span> <span>DISENGAGE AUTOPILOT</span>';
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

    // Send Motor Drive Command
    function sendDrive(action) {
      if (autopilotActive && action !== 'S') {
        // Manual override disengages autopilot immediately
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

    // Touch & Hold Handlers for Smooth Driving
    document.querySelectorAll('.dpad-btn').forEach(btn => {
      const act = btn.getAttribute('data-action');
      
      const startAction = (e) => {
        e.preventDefault();
        btn.classList.add('pressed');
        sendDrive(act);
        if (act !== 'S') {
          // Keep sending every 200ms while held
          clearInterval(activePressInterval);
          activePressInterval = setInterval(() => sendDrive(act), 200);
        }
      };

      const stopAction = (e) => {
        e.preventDefault();
        btn.classList.remove('pressed');
        clearInterval(activePressInterval);
        if (act !== 'S') {
          sendDrive('S'); // Stop on release!
        }
      };

      btn.addEventListener('touchstart', startAction, {passive: false});
      btn.addEventListener('touchend', stopAction, {passive: false});
      btn.addEventListener('touchcancel', stopAction, {passive: false});
      btn.addEventListener('mousedown', startAction);
      btn.addEventListener('mouseup', stopAction);
      btn.addEventListener('mouseleave', stopAction);
    });

    // Keyboard Hotkey Fallback (W, A, S, D, F, Space)
    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      const k = e.key.toLowerCase();
      if (k === 'w' || k === 'arrowup') sendDrive('F');
      else if (k === 's' || k === 'arrowdown') sendDrive('B');
      else if (k === 'a' || k === 'arrowleft') sendDrive('L');
      else if (k === 'd' || k === 'arrowright') sendDrive('R');
      else if (k === ' ' || k === 'x') sendDrive('S');
      else if (k === 'f') toggleAutopilot();
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
          // Connection Badge
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

          // Action Telemetry
          document.getElementById('actionTelemetry').innerText = data.current_action;

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
        pass # Suppress noisy request logging

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
            # Low latency multipart MJPEG stream
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--frame')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()
            try:
                while True:
                    frame_bytes = get_current_frame()
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(frame_bytes)}\r\n\r\n".encode())
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b"\r\n")
                    time.sleep(0.04) # ~25 FPS
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
                    "speed": state.speed
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
