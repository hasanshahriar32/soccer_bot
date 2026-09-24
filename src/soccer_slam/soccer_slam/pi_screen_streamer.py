#!/usr/bin/env python3
"""
====================================================================
Soccer Bot Pi Screen Streamer Node
====================================================================
Streams real-time SLAM occupancy grid map, robot world pose, and
path trajectory to the Raspberry Pi built-in 480x320 LCD screen
over a low-latency TCP socket.
====================================================================
"""

import base64
import json
import math
import socket
import struct
import threading
import time
import zlib

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid, Path
from std_msgs.msg import Float32


def euler_from_quaternion(x, y, z, w):
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    return math.degrees(math.atan2(t3, t4))


class PiScreenStreamerNode(Node):
    def __init__(self):
        super().__init__('pi_screen_streamer')

        self.declare_parameter('port', 8765)
        self.port = self.get_parameter('port').get_parameter_value().integer_value

        # QoS for map (transient local)
        map_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )

        # Subscribers
        self.map_sub = self.create_subscription(OccupancyGrid, '/map', self.map_callback, map_qos)
        self.pose_sub = self.create_subscription(PoseStamped, '/robot_map_pose', self.pose_callback, 10)
        self.path_sub = self.create_subscription(Path, '/robot_trajectory', self.path_callback, 10)
        self.yaw_sub = self.create_subscription(Float32, '/phone_imu/yaw', self.yaw_callback, 10)

        # State
        self.lock = threading.Lock()
        self.latest_pose = {'x': 0.0, 'y': 0.0, 'yaw_deg': 0.0}
        self.latest_path = []
        self.latest_yaw = 0.0
        self.latest_map_packet = None
        self.has_new_map = False

        self.clients = []
        self.clients_lock = threading.Lock()

        # Start TCP Server thread
        threading.Thread(target=self.run_tcp_server, daemon=True).start()

        # 10 Hz broadcast timer for pose and telemetry
        self.timer = self.create_timer(0.1, self.broadcast_telemetry)

        self.get_logger().info(f"📺 [PI SCREEN STREAMER] Listening for Pi LCD client on port {self.port}...")

    def map_callback(self, msg: OccupancyGrid):
        try:
            w = msg.info.width
            h = msg.info.height
            res = msg.info.resolution
            ox = msg.info.origin.position.x
            oy = msg.info.origin.position.y

            raw_bytes = bytes([b & 0xFF for b in msg.data])
            compressed = zlib.compress(raw_bytes, level=1)
            b64_data = base64.b64encode(compressed).decode('ascii')

            packet = {
                'type': 'map',
                'width': w,
                'height': h,
                'resolution': res,
                'origin_x': ox,
                'origin_y': oy,
                'data': b64_data
            }

            with self.lock:
                self.latest_map_packet = packet
                self.has_new_map = True
        except Exception as e:
            self.get_logger().error(f"Error packing map: {e}")

    def pose_callback(self, msg: PoseStamped):
        with self.lock:
            q = msg.pose.orientation
            yaw = euler_from_quaternion(q.x, q.y, q.z, q.w)
            self.latest_pose = {
                'x': round(msg.pose.position.x, 3),
                'y': round(msg.pose.position.y, 3),
                'yaw_deg': round(yaw, 1)
            }

    def path_callback(self, msg: Path):
        poses = msg.poses
        step = max(1, len(poses) // 150)
        sampled = []
        for p in poses[::step]:
            sampled.append([round(p.pose.position.x, 2), round(p.pose.position.y, 2)])
        with self.lock:
            self.latest_path = sampled

    def yaw_callback(self, msg: Float32):
        with self.lock:
            self.latest_yaw = round(msg.data, 1)

    def run_tcp_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.port))
        server.listen(5)

        while True:
            try:
                conn, addr = server.accept()
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.get_logger().info(f"📺 [CONNECTED] Raspberry Pi Screen client connected from {addr[0]}:{addr[1]}")
                with self.clients_lock:
                    self.clients.append(conn)

                # Send initial map immediately if available
                with self.lock:
                    map_pkt = self.latest_map_packet
                if map_pkt:
                    self.send_packet_to_client(conn, map_pkt)
            except Exception as e:
                self.get_logger().warn(f"TCP accept error: {e}")

    def send_packet_to_client(self, conn, packet_dict):
        try:
            raw_json = json.dumps(packet_dict).encode('utf-8')
            msg = struct.pack('!I', len(raw_json)) + raw_json
            conn.sendall(msg)
            return True
        except Exception:
            return False

    def broadcast_telemetry(self):
        with self.clients_lock:
            if not self.clients:
                return
            active_clients = list(self.clients)

        with self.lock:
            pose = self.latest_pose
            path = self.latest_path
            phone_yaw = self.latest_yaw
            new_map = self.has_new_map
            map_pkt = self.latest_map_packet
            self.has_new_map = False

        # 1. Send map update if new map arrived
        if new_map and map_pkt:
            dead_clients = []
            for c in active_clients:
                if not self.send_packet_to_client(c, map_pkt):
                    dead_clients.append(c)
            if dead_clients:
                with self.clients_lock:
                    for d in dead_clients:
                        if d in self.clients:
                            self.clients.remove(d)

        # 2. Send 10 Hz telemetry
        telem_pkt = {
            'type': 'telemetry',
            'pose': pose,
            'path': path,
            'phone_yaw': phone_yaw,
            'stamp': time.time()
        }

        dead_clients = []
        for c in active_clients:
            if not self.send_packet_to_client(c, telem_pkt):
                dead_clients.append(c)

        if dead_clients:
            with self.clients_lock:
                for d in dead_clients:
                    if d in self.clients:
                        self.clients.remove(d)


def main(args=None):
    rclpy.init(args=args)
    node = PiScreenStreamerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
