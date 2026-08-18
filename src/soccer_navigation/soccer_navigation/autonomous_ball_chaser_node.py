#!/usr/bin/env python3
"""
====================================================================
  FULL 360° 12-INCH PROXIMITY WHEEL CONTROLLER — ROS 2 JAZZY
====================================================================
Description:
    Connected directly to Raspberry Pi Physical Motor Server (Port 9000).
    
    1. Distance Threshold: 12 inches (30.48 cm / 0.3048 m).
    2. Checks ALL Lidar 360° angles + Camera Ball Tracker for objects.
    3. WHEN OBJECT DETECTED WITHIN 12 INCHES (<= 0.3048m):
       -> STOPS PHYSICAL WHEELS INSTANTLY ('S').
    4. WHEN NO OBJECT WITHIN 12 INCHES (> 0.3048m):
       -> MOVES/SPINS PHYSICAL WHEELS ('F' or 'R').
====================================================================
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import Point, Twist
from sensor_msgs.msg import LaserScan
import socket
import threading
import time

STOP_DISTANCE_METERS = 0.3048  # 12 inches = 0.3048 m

class PhysicalWheel12InchController(Node):
    def __init__(self):
        super().__init__('physical_wheel_12inch_controller')

        self.pi_ip = '192.168.0.135'
        self.motor_port = 9000
        self.motor_sock = None
        self.sock_lock = threading.Lock()

        # Connect to physical motor server on Pi
        self.connect_pi_motors()

        # Subscriptions
        self.sub_ball = self.create_subscription(
            Point, '/ball_position', self.ball_callback, 10)
        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        # State tracking
        self.ball_distance_m = 99.0
        self.ball_pixel_offset = 0.0
        self.last_ball_time = 0.0
        self.lidar_min_dist_m = 99.0
        self.last_command_sent = None

        # Control Loop Timer (20Hz = 50ms)
        self.timer = self.create_timer(0.05, self.control_loop)

        self.get_logger().info('====================================================')
        self.get_logger().info(' FULL 360° 12-INCH PROXIMITY WHEEL CONTROLLER READY  ')
        self.get_logger().info(f' Stop Threshold: 12 inches ({STOP_DISTANCE_METERS:.2f} meters)')
        self.get_logger().info('====================================================')

    def connect_pi_motors(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)
            s.connect((self.pi_ip, self.motor_port))
            s.sendall(b'3\n') # Set speed level 3
            self.motor_sock = s
            self.get_logger().info(f"[HARDWARE] Connected to Physical Motor Server at {self.pi_ip}:{self.motor_port}!")
        except Exception as e:
            self.get_logger().warn(f"[HARDWARE] Motor Server at {self.pi_ip}:{self.motor_port} unavailable ({e}). Running on /cmd_vel.")
            self.motor_sock = None

    def send_hardware_motor_cmd(self, cmd_char):
        if cmd_char == self.last_command_sent:
            return
        self.last_command_sent = cmd_char
        
        with self.sock_lock:
            if self.motor_sock:
                try:
                    self.motor_sock.sendall(f"{cmd_char}\n".encode())
                except:
                    self.motor_sock = None

    def scan_callback(self, msg):
        ranges = msg.ranges
        if len(ranges) == 0:
            return

        # Check ALL 360 degree Lidar range readings
        valid_ranges = [r for r in ranges if 0.05 < r < 20.0]
        if valid_ranges:
            self.lidar_min_dist_m = min(valid_ranges)
        else:
            self.lidar_min_dist_m = 99.0

    def ball_callback(self, msg):
        self.last_ball_time = time.time()
        self.ball_distance_m = msg.x
        self.ball_pixel_offset = msg.y

    def control_loop(self):
        if not rclpy.ok():
            return

        now = time.time()
        has_recent_ball = (now - self.last_ball_time) < 0.8

        # Overall closest object distance (from 360° Lidar or Camera Ball Tracker)
        closest_object_dist = self.lidar_min_dist_m
        if has_recent_ball and self.ball_distance_m < closest_object_dist:
            closest_object_dist = self.ball_distance_m

        twist = Twist()

        # -----------------------------------------------------------
        # RULE 1: OBJECT DETECTED WITHIN 12 INCHES (<= 0.3048m) -> STOP!
        # -----------------------------------------------------------
        if closest_object_dist <= STOP_DISTANCE_METERS:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.pub_cmd_vel.publish(twist)
            self.send_hardware_motor_cmd('S')
            
            dist_inches = closest_object_dist * 39.3701
            self.get_logger().info(
                f'[STOP] 🛑 OBJECT DETECTED WITHIN 12 INCHES ({dist_inches:.1f} in / {closest_object_dist:.2f}m)! PHYSICAL WHEELS STOPPED.',
                throttle_duration_sec=0.4
            )

        # -----------------------------------------------------------
        # RULE 2: NO OBJECT WITHIN 12 INCHES (> 0.3048m) -> MOVE / SPIN!
        # -----------------------------------------------------------
        else:
            if has_recent_ball:
                if abs(self.ball_pixel_offset) > 40:
                    cmd = 'L' if self.ball_pixel_offset < 0 else 'R'
                    twist.angular.z = -0.6 if self.ball_pixel_offset < 0 else 0.6
                else:
                    cmd = 'F'
                    twist.linear.x = 0.25
                
                self.send_hardware_motor_cmd(cmd)
                self.pub_cmd_vel.publish(twist)
                dist_inches = self.ball_distance_m * 39.3701
                self.get_logger().info(
                    f'[APPROACH] 🎯 Ball detected at {dist_inches:.1f} in ({self.ball_distance_m:.2f}m) > 12 in. Driving ({cmd})!',
                    throttle_duration_sec=0.4
                )
            else:
                # No object seen within 12 inches -> Spin wheels to search!
                twist.angular.z = 0.65
                self.send_hardware_motor_cmd('R')
                self.pub_cmd_vel.publish(twist)
                dist_inches = closest_object_dist * 39.3701 if closest_object_dist < 90 else 999.0
                self.get_logger().info(
                    f'[AUTO SEARCH] 🔄 Nearest object at {dist_inches:.1f} in ({closest_object_dist:.2f}m) > 12 in. WHEELS MOVING/SPINNING TO SEARCH...',
                    throttle_duration_sec=0.4
                )

def main(args=None):
    rclpy.init(args=args)
    node = PhysicalWheel12InchController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.send_hardware_motor_cmd('S')
        node.destroy_node()

if __name__ == '__main__':
    main()
