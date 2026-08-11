import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import socket
import json
import math
import threading
import time

class LidarHub(Node):
    def __init__(self):
        super().__init__('lidar_hub')
        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        self.running = True
        
        self.thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.thread.start()
        self.get_logger().info("Lidar Hub Node started, connecting to Edge Lidar on Port 5000...")

    def receive_loop(self):
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4.0)
                sock.connect(('192.168.0.135', 5000))
                self.get_logger().info("Connected to Edge Lidar at 192.168.0.135:5000!")
                buffer = ""
                
                while self.running:
                    data = sock.recv(65536).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line and line.startswith("{"):
                            try:
                                scan_dict = json.loads(line)
                                self.publish_scan(scan_dict)
                            except:
                                pass
                sock.close()
            except Exception as e:
                time.sleep(1.0)

    def publish_scan(self, scan_dict):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'laser_frame'
        
        msg.angle_min = float(scan_dict.get('angle_min', 0.0))
        msg.angle_max = float(scan_dict.get('angle_max', 2.0 * math.pi))
        msg.angle_increment = float(scan_dict.get('angle_increment', math.pi / 180.0))
        msg.time_increment = float(scan_dict.get('time_increment', 0.0))
        msg.scan_time = float(scan_dict.get('scan_time', 0.1))
        msg.range_min = float(scan_dict.get('range_min', 0.08))
        msg.range_max = float(scan_dict.get('range_max', 10.0))
        
        if 'ranges' in scan_dict:
            msg.ranges = [float(r) for r in scan_dict['ranges']]
        else:
            ranges = [0.0] * 360
            for k, v in scan_dict.items():
                try:
                    angle = int(float(k))
                    if 0 <= angle < 360:
                        ranges[angle] = float(v)
                except:
                    pass
            msg.ranges = ranges
            
        if 'intensities' in scan_dict:
            msg.intensities = [float(i) for i in scan_dict['intensities']]
            
        self.pub.publish(msg)
        
        if not hasattr(self, '_pub_cnt'): self._pub_cnt = 0
        self._pub_cnt += 1
        if self._pub_cnt % 50 == 0:
            valid = len([r for r in msg.ranges if 0.12 < r < 8.0])
            self.get_logger().info(f"Published {self._pub_cnt} scans to /scan (Active valid points: {valid})")

def main(args=None):
    rclpy.init(args=args)
    node = LidarHub()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
