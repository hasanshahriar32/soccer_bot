import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data
import socket
import json
import threading
import time

class LidarBridgeNode(Node):
    def __init__(self):
        super().__init__('lidar_bridge_node')
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', 5000))
        self.server.listen(5)
        self.tcp_clients = []
        self.lock = threading.Lock()
        
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )
        self.get_logger().info("Lidar TCP Bridge Server listening on 0.0.0.0:5000...")
        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        while True:
            try:
                conn, addr = self.server.accept()
                with self.lock:
                    self.tcp_clients.append(conn)
                self.get_logger().info(f"Client connected to Lidar stream from {addr}")
            except:
                pass

    def scan_callback(self, msg: LaserScan):
        payload = {
            "header": {
                "frame_id": msg.header.frame_id,
                "stamp": {"sec": msg.header.stamp.sec, "nanosec": msg.header.stamp.nanosec}
            },
            "angle_min": msg.angle_min,
            "angle_max": msg.angle_max,
            "angle_increment": msg.angle_increment,
            "time_increment": msg.time_increment,
            "scan_time": msg.scan_time,
            "range_min": msg.range_min,
            "range_max": msg.range_max,
            "ranges": [round(float(r), 4) for r in msg.ranges],
            "intensities": [round(float(i), 1) for i in msg.intensities]
        }
        data = (json.dumps(payload) + "\n").encode('utf-8')
        with self.lock:
            dead = []
            for c in self.tcp_clients:
                try:
                    c.sendall(data)
                except:
                    dead.append(c)
            for d in dead:
                self.tcp_clients.remove(d)

def main():
    rclpy.init()
    node = LidarBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
