#!/usr/bin/env python3
"""
====================================================================
                YDLIDAR RAW TCP PACKET PARSER NODE
====================================================================
Description:
    ROS 2 node that connects to the Raspberry Pi Lidar TCP server
    on port 5000, parses YDLidar X4 raw byte frames (0xAA 0x55),
    calculates distance & angle readings, and publishes standard
    sensor_msgs/msg/LaserScan to the /scan topic.

Target Topic: /scan (frame_id: laser_frame)
====================================================================
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import socket
import math
import struct
import threading
import time

class RawLidarPublisher(Node):
    def __init__(self):
        super().__init__('raw_lidar_publisher')
        self.publisher_ = self.create_publisher(LaserScan, '/scan', 10)
        self.host = '192.168.0.135'
        self.port = 5000
        
        self.get_logger().info(f"Connecting to Lidar stream at {self.host}:{self.port}...")
        self.running = True
        self.thread = threading.Thread(target=self.receive_stream)
        self.thread.daemon = True
        self.thread.start()

    def receive_stream(self):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5.0)
                s.connect((self.host, self.port))
                self.get_logger().info("Connected to Lidar Stream successfully!")
                
                buffer = b''
                ranges = [float('inf')] * 360
                
                while self.running:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    
                    while len(buffer) >= 10:
                        header_idx = buffer.find(b'\xaa\x55')
                        if header_idx == -1:
                            buffer = buffer[-2:]
                            break
                            
                        if header_idx > 0:
                            buffer = buffer[header_idx:]
                            
                        if len(buffer) < 10:
                            break
                            
                        ls_byte = buffer[3]
                        sample_count = buffer[3]
                        packet_len = 10 + sample_count * 2
                        
                        if len(buffer) < packet_len:
                            break
                            
                        packet = buffer[:packet_len]
                        buffer = buffer[packet_len:]
                        
                        fsa = struct.unpack('<H', packet[4:6])[0] >> 1
                        lsa = struct.unpack('<H', packet[6:8])[0] >> 1
                        
                        start_angle = fsa / 64.0
                        end_angle = lsa / 64.0
                        
                        if end_angle < start_angle:
                            diff = (end_angle + 360.0) - start_angle
                        else:
                            diff = end_angle - start_angle
                            
                        step = diff / (sample_count - 1) if sample_count > 1 else 0
                        
                        for i in range(sample_count):
                            dist_mm = struct.unpack('<H', packet[10 + i*2 : 12 + i*2])[0] / 4.0
                            if dist_mm > 0:
                                angle = (start_angle + step * i) % 360.0
                                idx = int(round(angle)) % 360
                                dist_m = dist_mm / 1000.0
                                if 0.1 <= dist_m <= 10.0:
                                    ranges[idx] = dist_m
                                    
                        # Publish complete scan message
                        scan_msg = LaserScan()
                        scan_msg.header.stamp = self.get_clock().now().to_msg()
                        scan_msg.header.frame_id = 'laser_frame'
                        scan_msg.angle_min = 0.0
                        scan_msg.angle_max = 2.0 * math.pi
                        scan_msg.angle_increment = (2.0 * math.pi) / 360.0
                        scan_msg.time_increment = 0.0
                        scan_msg.scan_time = 0.1
                        scan_msg.range_min = 0.1
                        scan_msg.range_max = 10.0
                        scan_msg.ranges = list(ranges)
                        self.publisher_.publish(scan_msg)
                        
            except Exception as e:
                time.sleep(1.0)

def main(args=None):
    rclpy.init(args=args)
    node = RawLidarPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.running = False
        node.thread.join()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
