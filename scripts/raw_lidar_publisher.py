#!/usr/bin/env python3
"""
====================================================================
      YDLIDAR X4 RAW BYTE PARSER & ROS 2 PUBLISHER NODE
====================================================================
Description:
    Connects to the raw TCP stream from Raspberry Pi (Port 5000),
    parses YDLidar X4 packet headers (0xAA 0x55), decodes start/end
    angles & distance samples, and publishes sensor_msgs/LaserScan
    to the ROS 2 topic /scan.
====================================================================
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import socket
import struct
import math
import time
import threading

class RawLidarPublisher(Node):
    def __init__(self):
        super().__init__('raw_lidar_publisher')
        
        self.publisher_ = self.create_publisher(LaserScan, '/scan', 10)
        self.pi_ip = '10.73.75.146'
        self.port = 5000
        self.running = True
        
        self.get_logger().info(f"Connecting to Lidar stream at {self.pi_ip}:{self.port}...")
        self.thread = threading.Thread(target=self.receive_lidar_stream, daemon=True)
        self.thread.start()

    def receive_lidar_stream(self):
        scan_cnt = 0
        current_scan = [0.0] * 360
        
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((self.pi_ip, self.port))
                self.get_logger().info(f"Connected to Lidar Stream at {self.pi_ip}:{self.port} successfully!")
                
                buffer = b''
                while self.running:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    
                    while len(buffer) >= 10:
                        # Find YDLidar X4 sync header 0xAA 0x55
                        header_idx = buffer.find(b'\xaa\x55')
                        if header_idx == -1:
                            buffer = buffer[-1:]
                            break
                        if header_idx > 0:
                            buffer = buffer[header_idx:]
                            
                        if len(buffer) < 10:
                            break
                            
                        ct = buffer[2]
                        ls = buffer[3]
                        packet_len = 10 + (ls * 2)
                        
                        if len(buffer) < packet_len:
                            break
                            
                        pkt = buffer[:packet_len]
                        buffer = buffer[packet_len:]
                        
                        # Parse start and end angles
                        fsa = struct.unpack('<H', pkt[4:6])[0]
                        lsa = struct.unpack('<H', pkt[6:8])[0]
                        
                        start_angle = (fsa >> 1) / 64.0
                        end_angle = (lsa >> 1) / 64.0
                        
                        diff = end_angle - start_angle
                        if diff < 0:
                            diff += 360.0
                            
                        step = diff / (ls - 1) if ls > 1 else 0.0
                        
                        for i in range(ls):
                            dist_raw = struct.unpack('<H', pkt[10 + i*2 : 12 + i*2])[0]
                            dist_m = (dist_raw / 4.0) / 1000.0  # Convert mm to meters
                            
                            angle = start_angle + (step * i)
                            angle_idx = int(angle) % 360
                            
                            if 0.05 < dist_m < 10.0:
                                current_scan[angle_idx] = dist_m
                                
                        if ct & 0x01: # Zero packet bit indicating full 360 turn
                            self.publish_scan(current_scan)
                            scan_cnt += 1
                            if scan_cnt % 100 == 0:
                                self.get_logger().info(f"Published {scan_cnt} 360 scans to /scan")
                            current_scan = [0.0] * 360

                sock.close()
            except Exception as e:
                time.sleep(1.0)

    def publish_scan(self, scan_data):
        scan_msg = LaserScan()
        scan_msg.header.stamp = self.get_clock().now().to_msg()
        scan_msg.header.frame_id = 'laser_frame'
        
        scan_msg.angle_min = 0.0
        scan_msg.angle_max = 2.0 * math.pi
        scan_msg.angle_increment = (2.0 * math.pi) / 360.0
        scan_msg.time_increment = 0.0
        scan_msg.scan_time = 0.1
        scan_msg.range_min = 0.08
        scan_msg.range_max = 10.0
        
        scan_msg.ranges = scan_data
        self.publisher_.publish(scan_msg)

def main(args=None):
    rclpy.init(args=args)
    node = RawLidarPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.running = False
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
