#!/usr/bin/env python3
"""
====================================================================
Soccer Bot Phone IMU & Gyroscope ROS 2 Bridge Node
====================================================================
Streams high-frequency orientation and gyroscope telemetry from any
smartphone (Android / iOS) over local Wi-Fi into ROS 2 at 50-100 Hz.

Key Features:
  1. Built-in Web Server (Port 8080): Open in phone browser, tap to stream.
  2. Built-in UDP Listener (Port 5555): Compatible with HyperIMU / Phyphox.
  3. Real-Time TF Broadcast: Publishes dynamic 'odom' -> 'base_link' rotation.
  4. ROS 2 Topics:
     - /imu/data        (sensor_msgs/msg/Imu)
     - /odom            (nav_msgs/msg/Odometry)
     - /phone_imu/yaw   (std_msgs/msg/Float32)
====================================================================
"""

import asyncio
import io
import json
import math
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import qrcode
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped, Quaternion
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32
from tf2_ros import TransformBroadcaster
import websockets


def get_local_ip():
    """Detect local LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def quaternion_from_euler(roll, pitch, yaw):
    """Convert Euler angles (radians) to quaternion (x, y, z, w)."""
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    q = Quaternion()
    q.w = cr * cp * cy + sr * sp * sy
    q.x = sr * cp * cy - cr * sp * sy
    q.y = cr * sp * cy + sr * cp * sy
    q.z = cr * cp * sy - sr * sp * cy
    return q


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Soccer Bot IMU</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0d1117; color: #c9d1d9; min-height: 100vh;
    display: flex; flex-direction: column; align-items: center; justify-content: space-between;
    padding: 20px; text-align: center;
  }
  .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 16px;
    padding: 24px; width: 100%; max-width: 400px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  }
  h1 { font-size: 1.4rem; color: #58a6ff; margin-bottom: 8px; }
  .badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 0.85rem; font-weight: bold; margin-bottom: 16px;
    background: #21262d; color: #8b949e;
  }
  .badge.connected { background: #238636; color: #ffffff; }
  .compass-box {
    position: relative; width: 180px; height: 180px; margin: 15px auto;
    border: 3px solid #30363d; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; background: #0d1117;
  }
  .needle {
    position: absolute; width: 4px; height: 80px; background: #f85149;
    border-radius: 2px; transform-origin: 50% 100%; top: 10px;
    transition: transform 0.05s linear;
  }
  .angle-display { font-size: 2.2rem; font-weight: 800; color: #58a6ff; font-mono: monospace; }
  .angle-unit { font-size: 1rem; color: #8b949e; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
  .val-box { background: #0d1117; border-radius: 8px; padding: 10px; border: 1px solid #21262d; }
  .val-title { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; }
  .val-num { font-size: 1.1rem; font-weight: bold; color: #e6edf3; }
  .btn {
    width: 100%; padding: 14px; margin-top: 12px; border: none; border-radius: 8px;
    font-size: 1rem; font-weight: bold; cursor: pointer; transition: all 0.2s;
  }
  .btn-start { background: #238636; color: white; }
  .btn-start:active { background: #2ea043; }
  .btn-zero { background: #1f6feb; color: white; }
  .btn-zero:active { background: #388bfd; }
  .footer { font-size: 0.8rem; color: #484f58; margin-top: 20px; }
</style>
</head>
<body>

<div class="card">
  <h1>⚽ Soccer Bot Gyro</h1>
  <div id="statusBadge" class="badge">DISCONNECTED</div>

  <div class="compass-box">
    <div id="needle" class="needle"></div>
    <div>
      <div id="yawDisplay" class="angle-display">0.0°</div>
      <div class="angle-unit">HEADING</div>
    </div>
  </div>

  <div class="grid">
    <div class="val-box">
      <div class="val-title">Rate (Z)</div>
      <div id="rateZ" class="val-num">0.0 °/s</div>
    </div>
    <div class="val-box">
      <div class="val-title">Hz</div>
      <div id="hzDisplay" class="val-num">0 Hz</div>
    </div>
  </div>

  <button id="btnStart" class="btn btn-start">🚀 Start Gyro Streaming</button>
  <button id="btnZero" class="btn btn-zero" style="display:none;">🎯 Zero Heading (Tare)</button>
</div>

<div class="footer">
  Keep phone level with LiDAR sensor | Auto-Reconnect Active
</div>

<script>
  let ws = null;
  let isStreaming = false;
  let tareOffset = 0.0;
  let currentYaw = 0.0;
  let sampleCount = 0;
  let lastHzTime = performance.now();

  const statusBadge = document.getElementById('statusBadge');
  const yawDisplay = document.getElementById('yawDisplay');
  const rateZ = document.getElementById('rateZ');
  const hzDisplay = document.getElementById('hzDisplay');
  const needle = document.getElementById('needle');
  const btnStart = document.getElementById('btnStart');
  const btnZero = document.getElementById('btnZero');

  function connectWebSocket() {
    const proto = (window.location.protocol === 'https:') ? 'wss:' : 'ws:';
    const wsUrl = proto + '//' + window.location.hostname + ':8081';
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      statusBadge.textContent = '● STREAMING ACTIVE';
      statusBadge.className = 'badge connected';
    };

    ws.onclose = () => {
      statusBadge.textContent = 'RECONNECTING...';
      statusBadge.className = 'badge';
      setTimeout(connectWebSocket, 1500);
    };
  }

  async function requestPermissionsAndStart() {
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
      try {
        const response = await DeviceOrientationEvent.requestPermission();
        if (response !== 'granted') {
          alert('Permission required for motion sensors');
          return;
        }
      } catch (e) {
        console.error(e);
      }
    }

    connectWebSocket();

    window.addEventListener('deviceorientation', (e) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      
      let rawAlpha = e.alpha || 0; // 0 to 360
      let beta = e.beta || 0;
      let gamma = e.gamma || 0;

      // Compensate tare offset
      let relYaw = (rawAlpha - tareOffset + 360) % 360;
      if (relYaw > 180) relYaw -= 360; // -180 to +180

      currentYaw = -relYaw; // CCW positive for ROS standard
      yawDisplay.textContent = currentYaw.toFixed(1) + '°';
      needle.style.transform = `rotate(${-currentYaw}deg)`;

      sampleCount++;
      const now = performance.now();
      if (now - lastHzTime >= 1000) {
        hzDisplay.textContent = sampleCount + ' Hz';
        sampleCount = 0;
        lastHzTime = now;
      }

      const payload = {
        type: 'orientation',
        yaw: currentYaw,
        pitch: beta,
        roll: gamma,
        stamp: Date.now() / 1000.0
      };
      ws.send(JSON.stringify(payload));
    }, true);

    window.addEventListener('devicemotion', (e) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      const rot = e.rotationRate || {};
      const gz = rot.gamma || rot.alpha || 0; // deg/s
      rateZ.textContent = gz.toFixed(1) + ' °/s';

      const payload = {
        type: 'motion',
        gyro_z: -gz * (Math.PI / 180.0), // rad/s
        acc_x: (e.accelerationIncludingGravity && e.accelerationIncludingGravity.x) || 0,
        acc_y: (e.accelerationIncludingGravity && e.accelerationIncludingGravity.y) || 0,
        acc_z: (e.accelerationIncludingGravity && e.accelerationIncludingGravity.z) || 0
      };
      ws.send(JSON.stringify(payload));
    }, true);

    btnStart.style.display = 'none';
    btnZero.style.display = 'block';
    isStreaming = true;
  }

  btnStart.addEventListener('click', requestPermissionsAndStart);
  btnZero.addEventListener('click', () => {
    tareOffset = (tareOffset - currentYaw + 360) % 360;
  });
</script>
</body>
</html>
"""


class WebPageHandler(BaseHTTPRequestHandler):
    """Serves the mobile web page."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode('utf-8'))

    def log_message(self, format, *args):
        pass  # Suppress HTTP access noise


class PhoneImuBridgeNode(Node):
    def __init__(self):
        super().__init__('phone_imu_bridge')

        self.declare_parameter('http_port', 8080)
        self.declare_parameter('ws_port', 8081)
        self.declare_parameter('udp_port', 5555)
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        self.http_port = self.get_parameter('http_port').get_parameter_value().integer_value
        self.ws_port = self.get_parameter('ws_port').get_parameter_value().integer_value
        self.udp_port = self.get_parameter('udp_port').get_parameter_value().integer_value
        self.publish_tf = self.get_parameter('publish_tf').get_parameter_value().bool_value
        self.odom_frame = self.get_parameter('odom_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value

        self.local_ip = get_local_ip()

        # Publishers
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.yaw_pub = self.create_publisher(Float32, '/phone_imu/yaw', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # State
        self.current_yaw_rad = 0.0
        self.current_pitch_rad = 0.0
        self.current_roll_rad = 0.0
        self.gyro_z = 0.0
        self.last_msg_time = self.get_clock().now()

        # 50 Hz timer for continuous TF and Odom broadcast
        self.timer = self.create_timer(0.02, self.publish_telemetry)

        # Start servers in background threads
        self.start_http_server()
        self.start_websocket_server()
        self.start_udp_server()

        self.print_welcome_banner()

    def print_welcome_banner(self):
        url = f"http://{self.local_ip}:{self.http_port}"
        self.get_logger().info("=" * 60)
        self.get_logger().info("📱 [PHONE IMU GYROSCOPE BRIDGE READY]")
        self.get_logger().info(f"👉 Open in Phone Browser: \033[1;32m{url}\033[0m")
        self.get_logger().info("=" * 60)

        # Print ASCII QR code in terminal
        try:
            qr = qrcode.QRCode()
            qr.add_data(url)
            qr.make()
            f = io.StringIO()
            qr.print_ascii(out=f, invert=True)
            f.seek(0)
            self.get_logger().info("\n" + f.read())
        except Exception:
            pass

    def start_http_server(self):
        def run_http():
            server = HTTPServer(('0.0.0.0', self.http_port), WebPageHandler)
            server.serve_forever()

        t = threading.Thread(target=run_http, daemon=True)
        t.start()

    def start_websocket_server(self):
        async def handle_client(websocket):
            self.get_logger().info("📱 [CONNECTED] Phone connected to WebSocket IMU stream!")
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'orientation':
                        deg = float(data.get('yaw', 0.0))
                        self.current_yaw_rad = math.radians(deg)
                        self.current_pitch_rad = math.radians(float(data.get('pitch', 0.0)))
                        self.current_roll_rad = math.radians(float(data.get('roll', 0.0)))
                    elif data.get('type') == 'motion':
                        self.gyro_z = float(data.get('gyro_z', 0.0))
                except Exception as e:
                    pass

        def run_ws():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            start_server = websockets.serve(handle_client, '0.0.0.0', self.ws_port)
            loop.run_until_complete(start_server)
            loop.run_forever()

        t = threading.Thread(target=run_ws, daemon=True)
        t.start()

    def start_udp_server(self):
        def run_udp():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('0.0.0.0', self.udp_port))
            while True:
                data, _ = sock.recvfrom(2048)
                try:
                    text = data.decode('utf-8').strip()
                    # Support CSV format: "yaw,pitch,roll,gz"
                    parts = text.split(',')
                    if len(parts) >= 3:
                        self.current_yaw_rad = math.radians(float(parts[0]))
                        self.current_pitch_rad = math.radians(float(parts[1]))
                        self.current_roll_rad = math.radians(float(parts[2]))
                        if len(parts) >= 4:
                            self.gyro_z = math.radians(float(parts[3]))
                except Exception:
                    pass

        t = threading.Thread(target=run_udp, daemon=True)
        t.start()

    def publish_telemetry(self):
        now = self.get_clock().now()
        q = quaternion_from_euler(self.current_roll_rad, self.current_pitch_rad, self.current_yaw_rad)

        # 1. Publish /imu/data
        imu_msg = Imu()
        imu_msg.header.stamp = now.to_msg()
        imu_msg.header.frame_id = 'imu_link'
        imu_msg.orientation = q
        imu_msg.angular_velocity.z = self.gyro_z
        self.imu_pub.publish(imu_msg)

        # 2. Publish /phone_imu/yaw (in degrees for easy monitoring)
        yaw_msg = Float32()
        yaw_msg.data = math.degrees(self.current_yaw_rad)
        self.yaw_pub.publish(yaw_msg)

        # 3. Publish /odom
        odom_msg = Odometry()
        odom_msg.header.stamp = now.to_msg()
        odom_msg.header.frame_id = self.odom_frame
        odom_msg.child_frame_id = self.base_frame
        odom_msg.pose.pose.orientation = q
        odom_msg.twist.twist.angular.z = self.gyro_z
        self.odom_pub.publish(odom_msg)

        # 4. Broadcast dynamic TF odom -> base_link
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = now.to_msg()
            t.header.frame_id = self.odom_frame
            t.child_frame_id = self.base_frame
            t.transform.translation.x = 0.0
            t.transform.translation.y = 0.0
            t.transform.translation.z = 0.0
            t.transform.rotation = q
            self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = PhoneImuBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
