import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import serial
import math
import time

class PythonLidarNode(Node):
    def __init__(self):
        super().__init__('python_lidar_node')
        self.publisher_ = self.create_publisher(LaserScan, 'scan', 10)
        
        self.port = '/dev/ttyUSB0'
        self.baudrate = 115200
        
        self.get_logger().info(f"Connecting to Lidar on {self.port} at {self.baudrate}")
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
        except Exception as e:
            self.get_logger().error(f"Failed to open port: {e}")
            return
            
        # Stop scan
        self.ser.write(b'\xA5\x65')
        time.sleep(0.5)
        self.ser.flushInput()
        
        # Start scan
        self.ser.write(b'\xA5\x60')
        time.sleep(0.5)
        
        self.timer = self.create_timer(0.1, self.read_scan)
        self.get_logger().info("Lidar scanning started!")

    def read_scan(self):
        # Extremely simplified stub for parsing YDLidar protocol (or we can just use PyLidar3)
        # To avoid reinventing the complex protocol, let's just use the PyLidar3 library if installed!
        pass

def main(args=None):
    rclpy.init(args=args)
    node = PythonLidarNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
