import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import socket
import math

class RawLidarPublisher(Node):
    def __init__(self):
        super().__init__('raw_lidar_publisher')
        self.pub = self.create_publisher(LaserScan, 'scan', 10)
        self.host = '192.168.0.135'
        self.port = 5000
        
        self.get_logger().info(f"Connecting to Lidar stream at {self.host}:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
            self.get_logger().info("Connected to Lidar Stream successfully!")
        except Exception as e:
            self.get_logger().error(f"Failed to connect: {e}")
            return
            
        self.buffer = bytearray()
        self.current_scan = [0.0] * 360
        self.timer = self.create_timer(0.01, self.read_and_parse)

    def read_and_parse(self):
        try:
            data = self.sock.recv(4096)
            if not data:
                return
            self.buffer.extend(data)
            
            while len(self.buffer) > 10:
                # Find packet header 0xAA 0x55
                idx = -1
                for i in range(len(self.buffer) - 1):
                    if self.buffer[i] == 0xAA and self.buffer[i+1] == 0x55:
                        idx = i
                        break
                        
                if idx == -1:
                    self.buffer = self.buffer[-1:]
                    break
                    
                if idx > 0:
                    self.buffer = self.buffer[idx:]
                    
                if len(self.buffer) < 10:
                    break
                    
                ls = self.buffer[3]
                pkt_len = 10 + (ls * 2)
                if len(self.buffer) < pkt_len:
                    break
                    
                pkt = self.buffer[:pkt_len]
                self.buffer = self.buffer[pkt_len:]
                
                fsa = (pkt[5] << 8 | pkt[4]) >> 1
                lsa = (pkt[7] << 8 | pkt[6]) >> 1
                
                start_angle = (fsa / 64.0) % 360.0
                end_angle = (lsa / 64.0) % 360.0
                
                if end_angle < start_angle:
                    diff = (end_angle + 360.0) - start_angle
                else:
                    diff = end_angle - start_angle
                    
                angle_step = diff / max(1, (ls - 1))
                
                for i in range(ls):
                    raw_dist = (pkt[9 + (i*2)] << 8 | pkt[8 + (i*2)]) / 4.0 # mm
                    ang = int(round(start_angle + (i * angle_step))) % 360
                    if 100.0 < raw_dist < 10000.0:
                        self.current_scan[ang] = raw_dist / 1000.0 # m
                        
                # Publish scan periodically
                if pkt[2] & 0x01: # Sync packet
                    self.publish_scan()
                    
        except Exception as e:
            pass

    def publish_scan(self):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'laser_frame'
        msg.angle_min = 0.0
        msg.angle_max = 2.0 * math.pi
        msg.angle_increment = math.pi / 180.0
        msg.range_min = 0.1
        msg.range_max = 10.0
        msg.ranges = list(self.current_scan)
        self.pub.publish(msg)
        self.current_scan = [0.0] * 360

def main(args=None):
    rclpy.init(args=args)
    node = RawLidarPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
