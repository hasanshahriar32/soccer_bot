#!/usr/bin/env python3
"""
====================================================================
Soccer Bot Phone IMU & Gyroscope ROS 2 Bridge Node
====================================================================
Streams high-frequency orientation and gyroscope telemetry from any
smartphone (Android / iOS) over local Wi-Fi into ROS 2 at 50-100 Hz.

Supports:
  1. HTTPS (Port 8443) & HTTP (Port 8080) with auto-permission request.
  2. WSS & WS WebSockets for secure mobile browser streaming.
  3. UDP (Port 5555) for mobile apps like Phyphox / HyperIMU.
  4. Real-Time Dynamic TF (odom -> base_link) & ROS 2 /imu/data.
====================================================================
"""

import asyncio
import io
import json
import math
import os
import socket
import ssl
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


CERT_FILE = '/home/sharmin/Desktop/iot/soccer_bot/certs/cert.pem'
KEY_FILE = '/home/sharmin/Desktop/iot/soccer_bot/certs/key.pem'


def get_local_ip():
    """Detect local LAN / Hotspot IP address."""
    for target in [('10.72.30.146', 80), ('8.8.8.8', 80), ('10.255.255.255', 1)]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(target)
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith('127.'):
                return ip
        except Exception:
            pass
    return '127.0.0.1'


def quaternion_from_euler(roll, pitch, yaw):
    """Convert Euler angles (radians) to quaternion (x, y, z, w)."""
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    q = Quaternion()
    q.w = cr * cp * cy + sr * cp * sy
    q.x = sr * cp * cy - cr * sp * sy
    q.y = cr * sp * cy + sr * cp * sy
    q.z = cr * cp * sy - sr * sp * cy
    return q


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>⚽ Soccer Bot IMU</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0d1117; color: #c9d1d9; min-height: 100vh;
    display: flex; flex-direction: column; align-items: center; justify-content: flex-start;
    padding: 16px; text-align: center;
  }
  .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 16px;
    padding: 20px; width: 100%; max-width: 420px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    margin-bottom: 16px;
  }
  h1 { font-size: 1.3rem; color: #58a6ff; margin-bottom: 6px; }
  .badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 0.82rem; font-weight: bold; margin-bottom: 12px;
    background: #21262d; color: #8b949e;
  }
  .badge.connected { background: #238636; color: #ffffff; }
  .badge.error { background: #da3633; color: #ffffff; }
  
  .alert-box {
    background: #382405; border: 1px solid #9e6a03; color: #f0883e;
    border-radius: 10px; padding: 12px; font-size: 0.85rem; margin-bottom: 14px;
    text-align: left; line-height: 1.4; display: none;
  }
  .alert-box a { color: #58a6ff; font-weight: bold; text-decoration: underline; }

  .compass-box {
    position: relative; width: 170px; height: 170px; margin: 10px auto;
    border: 3px solid #30363d; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; background: #0d1117;
  }
  .needle {
    position: absolute; width: 4px; height: 75px; background: #f85149;
    border-radius: 2px; transform-origin: 50% 100%; top: 10px;
    transition: transform 0.05s linear;
  }
  .angle-display { font-size: 2.2rem; font-weight: 800; color: #58a6ff; font-family: monospace; }
  .angle-unit { font-size: 0.8rem; color: #8b949e; letter-spacing: 1px; }

  .diag-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px;
  }
  .diag-box {
    background: #0d1117; border-radius: 8px; padding: 8px; border: 1px solid #21262d;
    font-size: 0.75rem; text-align: left;
  }
  .diag-title { color: #8b949e; font-weight: bold; }
  .diag-val { color: #58a6ff; font-family: monospace; font-size: 0.95rem; margin-top: 2px; }

  .btn {
    width: 100%; padding: 14px; margin-top: 10px; border: none; border-radius: 8px;
    font-size: 1rem; font-weight: bold; cursor: pointer; transition: all 0.2s;
  }
  .btn-start { background: #238636; color: white; }
  .btn-start:active { background: #2ea043; }
  .btn-zero { background: #1f6feb; color: white; }
  .btn-zero:active { background: #388bfd; }
  .btn-https { background: #8957e5; color: white; text-decoration: none; display: block; text-align: center; }

  .footer { font-size: 0.78rem; color: #8b949e; max-width: 420px; line-height: 1.4; }
  .footer code { background: #161b22; padding: 2px 6px; border-radius: 4px; color: #79c0ff; }
</style>
</head>
<body>

<div class="card">
  <h1>⚽ Soccer Bot Phone Gyro</h1>
  <div id="statusBadge" class="badge">INITIALIZING...</div>

  <!-- HTTPS Security Warning if accessed via HTTP -->
  <div id="httpsWarning" class="alert-box">
    ⚠️ <b>Mobile Security Alert:</b> Modern phones (iOS / Android 12+) block hardware gyroscopes on non-HTTPS pages.<br><br>
    👉 <a id="httpsLink" href="#">Tap here to switch to Secure HTTPS</a>, then tap <i>Advanced → Proceed</i> to allow sensor access!
  </div>

  <div class="compass-box">
    <div id="needle" class="needle"></div>
    <div>
      <div id="yawDisplay" class="angle-display">0.0°</div>
      <div class="angle-unit">HEADING (YAW)</div>
      <div id="directionInfo" style="font-size: 0.75rem; color: #8b949e; margin-top: 4px; font-weight: bold;">⏸ Centered (0°)</div>
    </div>
  </div>

  <div class="diag-grid">
    <div class="diag-box">
      <div class="diag-title">RAW ALPHA (COMPASS)</div>
      <div id="rawAlpha" class="diag-val">0.0°</div>
    </div>
    <div class="diag-box">
      <div class="diag-title">RATE (GYRO Z)</div>
      <div id="rateZ" class="diag-val">0.0 °/s</div>
    </div>
    <div class="diag-box">
      <div class="diag-title">STREAM RATE</div>
      <div id="hzDisplay" class="diag-val">0 Hz</div>
    </div>
    <div class="diag-box">
      <div class="diag-title">PACKETS SENT</div>
      <div id="packetsDisplay" class="diag-val">0</div>
    </div>
  </div>

  <button id="btnStart" class="btn btn-start">🚀 Allow Sensors & Start Gyro</button>
  <div style="display: flex; gap: 8px; margin-top: 10px;">
    <button id="btnZero" class="btn btn-zero" style="display:none; flex: 1; margin-top: 0;">🎯 Zero Heading</button>
    <button id="btnInvert" class="btn" style="display:none; flex: 1; margin-top: 0; background: #238636; color: white;">🔄 Mode: Normal (+)</button>
  </div>
</div>

<div class="footer">
  <b>Setup Instructions:</b><br>
  1. Mount phone <b>flat & facing forward</b> on robot chassis.<br>
  2. Tap <b>Zero Heading</b> to calibrate robot forward heading.<br>
  3. Turn Left: Heading should show <b>+ (positive)</b>.<br>
  4. If Left turn shows <b>- (negative)</b>, tap <b>🔄 Mode</b> to invert!
</div>

<script>
  let ws = null;
  let isStreaming = false;
  let tareOffset = 0.0;
  let currentYaw = 0.0;
  let packetsSent = 0;
  let sampleCount = 0;
  let lastHzTime = performance.now();
  let eventsReceived = 0;

  const statusBadge = document.getElementById('statusBadge');
  const httpsWarning = document.getElementById('httpsWarning');
  const httpsLink = document.getElementById('httpsLink');
  const yawDisplay = document.getElementById('yawDisplay');
  const directionInfo = document.getElementById('directionInfo');
  const rawAlpha = document.getElementById('rawAlpha');
  const rateZ = document.getElementById('rateZ');
  const hzDisplay = document.getElementById('hzDisplay');
  const packetsDisplay = document.getElementById('packetsDisplay');
  const needle = document.getElementById('needle');
  const btnStart = document.getElementById('btnStart');
  const btnZero = document.getElementById('btnZero');
  const btnInvert = document.getElementById('btnInvert');

  // Check if loaded over HTTPS vs HTTP
  const isHttps = (window.location.protocol === 'https:');
  const host = window.location.hostname;
  
  if (!isHttps) {
    httpsLink.href = 'https://' + host + ':8443';
    httpsWarning.style.display = 'block';
    statusBadge.textContent = 'HTTP (INSECURE CONTEXT)';
    statusBadge.className = 'badge error';
  } else {
    statusBadge.textContent = 'READY TO CONNECT';
    statusBadge.className = 'badge';
  }

  function connectWebSocket() {
    const proto = isHttps ? 'wss:' : 'ws:';
    const wsPort = isHttps ? '8444' : '8081';
    const wsUrl = proto + '//' + host + ':' + wsPort;

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        statusBadge.textContent = '● STREAMING ACTIVE TO ROS 2';
        statusBadge.className = 'badge connected';
      };
      ws.onerror = (e) => {
        statusBadge.textContent = 'WS ERROR';
        statusBadge.className = 'badge error';
      };
      ws.onclose = () => {
        if (isStreaming) {
          statusBadge.textContent = 'RECONNECTING...';
          statusBadge.className = 'badge';
          setTimeout(connectWebSocket, 1500);
        }
      };
    } catch(e) {
      console.error(e);
    }
  }

  async function requestPermissionsAndStart() {
    // 1. iOS 13+ explicit permission request
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
      try {
        const response = await DeviceOrientationEvent.requestPermission();
        if (response !== 'granted') {
          alert('Sensor permission: ' + response + '. Please allow motion access in iOS Settings > Safari.');
          return;
        }
      } catch (e) {
        alert('Permission error: ' + e);
        return;
      }
    }

    if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
      try {
        await DeviceMotionEvent.requestPermission();
      } catch(e) {}
    }

    connectWebSocket();

    // 2. Listen to device orientation
    window.addEventListener('deviceorientation', (e) => {
      eventsReceived++;
      const isIOS = (e.webkitCompassHeading !== null && e.webkitCompassHeading !== undefined);
      let raw = isIOS ? e.webkitCompassHeading : ((e.alpha !== null && e.alpha !== undefined) ? e.alpha : 0);
      let beta = e.beta || 0;
      let gamma = e.gamma || 0;

      rawAlpha.textContent = raw.toFixed(1) + '°';

      // Heading calculation with Tare offset
      let relYaw = (raw - tareOffset + 360) % 360;
      if (relYaw > 180) relYaw -= 360;

      // ROS REP-103 standard: Counter-Clockwise (Left) turn MUST be positive (+).
      // iOS webkitCompassHeading increases CLOCKWISE -> negate to make CCW positive.
      // Android / W3C standard e.alpha increases COUNTER-CLOCKWISE -> already positive for CCW.
      let baseYaw = isIOS ? -relYaw : relYaw;
      currentYaw = invertYaw ? -baseYaw : baseYaw;

      // Update UI displays
      const signPrefix = currentYaw > 0.05 ? '+' : '';
      yawDisplay.textContent = signPrefix + currentYaw.toFixed(1) + '°';
      
      // Update turn indicator
      if (Math.abs(currentYaw) > 1.0) {
        if (currentYaw > 0) {
          directionInfo.textContent = '⟲ Turning LEFT (CCW / +)';
          directionInfo.style.color = '#3fb950';
        } else {
          directionInfo.textContent = '⟳ Turning RIGHT (CW / -)';
          directionInfo.style.color = '#f85149';
        }
      } else {
        directionInfo.textContent = '⏸ Straight / Centered (0°)';
        directionInfo.style.color = '#8b949e';
      }

      // Compass needle shows room orientation relative to robot
      needle.style.transform = `rotate(${-currentYaw}deg)`;

      sampleCount++;
      const now = performance.now();
      if (now - lastHzTime >= 1000) {
        hzDisplay.textContent = sampleCount + ' Hz';
        sampleCount = 0;
        lastHzTime = now;
      }

      if (ws && ws.readyState === WebSocket.OPEN) {
        packetsSent++;
        packetsDisplay.textContent = packetsSent;
        ws.send(JSON.stringify({
          type: 'orientation',
          yaw: currentYaw,
          pitch: beta,
          roll: gamma,
          stamp: Date.now() / 1000.0
        }));
      }
    }, true);

    // 3. Listen to device motion (Gyroscope Rate)
    window.addEventListener('devicemotion', (e) => {
      const rot = e.rotationRate || {};
      const gz_raw = rot.alpha || rot.gamma || rot.beta || 0;
      const gz_sign = (invertYaw ? -1 : 1);
      const gz = gz_raw * gz_sign;
      rateZ.textContent = (gz > 0 ? '+' : '') + gz.toFixed(1) + ' °/s';

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'motion',
          gyro_z: gz * (Math.PI / 180.0),
          acc_x: (e.accelerationIncludingGravity && e.accelerationIncludingGravity.x) || 0,
          acc_y: (e.accelerationIncludingGravity && e.accelerationIncludingGravity.y) || 0,
          acc_z: (e.accelerationIncludingGravity && e.accelerationIncludingGravity.z) || 0
        }));
      }
    }, true);

    btnStart.style.display = 'none';
    btnZero.style.display = 'block';
    btnInvert.style.display = 'block';
    isStreaming = true;

    // Check after 2 seconds if events were blocked
    setTimeout(() => {
      if (eventsReceived === 0) {
        if (!isHttps) {
          alert('⚠️ Motion events blocked because page is not HTTPS. Please tap the Purple Link at the top to switch to HTTPS!');
        } else {
          alert('Sensor data not received. Please verify motion sensor permissions in your browser settings.');
        }
      }
    }, 2000);
  }

  let invertYaw = false;
  btnInvert.addEventListener('click', () => {
    invertYaw = !invertYaw;
    btnInvert.textContent = invertYaw ? '🔄 Mode: Inverted (-)' : '🔄 Mode: Normal (+)';
    btnInvert.style.background = invertYaw ? '#d29922' : '#238636';
    btnInvert.style.color = '#ffffff';
  });

  btnStart.addEventListener('click', requestPermissionsAndStart);
  btnZero.addEventListener('click', () => {
    // Current raw reading becomes the tare offset
    const curRaw = parseFloat(rawAlpha.textContent) || 0;
    tareOffset = curRaw;
    currentYaw = 0.0;
    yawDisplay.textContent = '+0.0°';
    directionInfo.textContent = '⏸ Zeroed / Centered';
    needle.style.transform = 'rotate(0deg)';
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'orientation',
        yaw: 0.0,
        pitch: 0.0,
        roll: 0.0,
        stamp: Date.now() / 1000.0
      }));
    }
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
        pass


class PhoneImuBridgeNode(Node):
    def __init__(self):
        super().__init__('phone_imu_bridge')

        self.declare_parameter('http_port', 8080)
        self.declare_parameter('https_port', 8443)
        self.declare_parameter('ws_port', 8081)
        self.declare_parameter('wss_port', 8444)
        self.declare_parameter('udp_port', 5555)
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        self.http_port = self.get_parameter('http_port').get_parameter_value().integer_value
        self.https_port = self.get_parameter('https_port').get_parameter_value().integer_value
        self.ws_port = self.get_parameter('ws_port').get_parameter_value().integer_value
        self.wss_port = self.get_parameter('wss_port').get_parameter_value().integer_value
        self.udp_port = self.get_parameter('udp_port').get_parameter_value().integer_value
        self.publish_tf = self.get_parameter('publish_tf').get_parameter_value().bool_value
        self.odom_frame = self.get_parameter('odom_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value

        self.local_ip = get_local_ip()

        # SSL setup
        self.ssl_context = None
        if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
            try:
                self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                self.ssl_context.load_cert_chain(CERT_FILE, KEY_FILE)
                self.get_logger().info("🔒 [SSL] Loaded certificate for secure HTTPS and WSS!")
            except Exception as e:
                self.get_logger().warn(f"Failed to load SSL certificates: {e}")

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
        self.msg_count = 0

        # 50 Hz timer for continuous TF and Odom broadcast
        self.timer = self.create_timer(0.02, self.publish_telemetry)

        # Start servers in background threads
        self.start_http_servers()
        self.start_websocket_servers()
        self.start_udp_server()

        self.print_welcome_banner()

    def print_welcome_banner(self):
        https_url = f"https://{self.local_ip}:{self.https_port}"
        http_url = f"http://{self.local_ip}:{self.http_port}"
        self.get_logger().info("=" * 65)
        self.get_logger().info("📱 [PHONE IMU GYROSCOPE BRIDGE READY]")
        self.get_logger().info(f"👉 \033[1;32mSECURE HTTPS (Recommended for Gyro):\033[0m {https_url}")
        self.get_logger().info(f"👉 Plain HTTP: {http_url}")
        self.get_logger().info(f"👉 UDP App Listener (Phyphox/HyperIMU): Port {self.udp_port}")
        self.get_logger().info("=" * 65)

        # Print ASCII QR code in terminal for HTTPS URL
        try:
            qr = qrcode.QRCode()
            qr.add_data(https_url)
            qr.make()
            f = io.StringIO()
            qr.print_ascii(out=f, invert=True)
            f.seek(0)
            self.get_logger().info("\n" + f.read())
        except Exception:
            pass

    def start_http_servers(self):
        # 1. Plain HTTP server
        def run_http():
            server = HTTPServer(('0.0.0.0', self.http_port), WebPageHandler)
            server.serve_forever()
        threading.Thread(target=run_http, daemon=True).start()

        # 2. Secure HTTPS server
        if self.ssl_context:
            def run_https():
                server = HTTPServer(('0.0.0.0', self.https_port), WebPageHandler)
                server.socket = self.ssl_context.wrap_socket(server.socket, server_side=True)
                server.serve_forever()
            threading.Thread(target=run_https, daemon=True).start()

    def start_websocket_servers(self):
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
                        self.msg_count += 1
                        if self.msg_count % 100 == 1:
                            self.get_logger().info(f"📱 [PHONE TELEMETRY] Live Heading: {deg:.1f}° | Fusing with SLAM!")
                    elif data.get('type') == 'motion':
                        self.gyro_z = float(data.get('gyro_z', 0.0))
                except Exception:
                    pass

        # WS (plain)
        def run_ws():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            start_server = websockets.serve(handle_client, '0.0.0.0', self.ws_port)
            loop.run_until_complete(start_server)
            loop.run_forever()
        threading.Thread(target=run_ws, daemon=True).start()

        # WSS (secure)
        if self.ssl_context:
            def run_wss():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                start_server = websockets.serve(handle_client, '0.0.0.0', self.wss_port, ssl=self.ssl_context)
                loop.run_until_complete(start_server)
                loop.run_forever()
            threading.Thread(target=run_wss, daemon=True).start()

    def start_udp_server(self):
        def run_udp():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('0.0.0.0', self.udp_port))
            while True:
                data, _ = sock.recvfrom(2048)
                try:
                    text = data.decode('utf-8').strip()
                    parts = text.split(',')
                    if len(parts) >= 3:
                        self.current_yaw_rad = math.radians(float(parts[0]))
                        self.current_pitch_rad = math.radians(float(parts[1]))
                        self.current_roll_rad = math.radians(float(parts[2]))
                        if len(parts) >= 4:
                            self.gyro_z = math.radians(float(parts[3]))
                        self.msg_count += 1
                except Exception:
                    pass
        threading.Thread(target=run_udp, daemon=True).start()

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
