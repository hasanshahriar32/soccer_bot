import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import socket
import json
import math
import select

class LidarHub(Node):
    def __init__(self):
        super().__init__('lidar_hub')
        self.pub = self.create_publisher(LaserScan, 'scan', 10)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.get_logger().info("Connecting to Edge Lidar at 192.168.0.135:5000...")
        try:
            self.sock.connect(('192.168.0.135', 5000))
            self.get_logger().info("Connected to Edge Lidar successfully!")
        except Exception as e:
            self.get_logger().error(f"Failed to connect: {e}")
            return
            
        self.sock.setblocking(0)
        self.timer = self.create_timer(0.02, self.read_data)
        self.buffer = ""

    def read_data(self):
        try:
            ready = select.select([self.sock], [], [], 0.01)
            if ready[0]:
                data = self.sock.recv(8192).decode('utf-8')
                if not data: return
                self.buffer += data
                while "\\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\\n", 1)
                    if line.strip():
                        scan_dict = json.loads(line)
                        self.publish_scan(scan_dict)
        except Exception as e:
            pass

    def publish_scan(self, scan_dict):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'laser_frame'
        msg.angle_min = 0.0
        msg.angle_max = 2 * math.pi
        msg.angle_increment = math.pi / 180.0
        msg.time_increment = 0.0
        msg.range_min = 0.12
        msg.range_max = 10.0
        
        ranges = [0.0] * 360
        for angle_str, dist in scan_dict.items():
            angle = int(angle_str)
            if 0 <= angle < 360:
                ranges[angle] = float(dist) / 1000.0 # mm to meters
                
        msg.ranges = ranges
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = LidarHub()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
