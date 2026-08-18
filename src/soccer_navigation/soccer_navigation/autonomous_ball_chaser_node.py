#!/usr/bin/env python3
"""
====================================================================
  12-INCH AUTOMATIC PHYSICAL WHEEL CONTROLLER — ROS 2 JAZZY
====================================================================
Description:
    Connected directly to Raspberry Pi Physical Motor Server (Port 9000).
    
    1. Threshold: 12 inches (30.48 cm / 0.3048 m).
    2. When POWERED ON / LAUNCHED:
       - Automatically moves/spins physical robot wheels.
    3. When OBJECT DETECTED WITHIN 12 INCHES (<= 0.30m):
       - INSTANTLY STOPS PHYSICAL WHEELS ('S').
    4. When NO OBJECT within 12 inches (> 0.30m):
       - RESUMES AUTOMATIC MOVEMENT ('F' / 'R').
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

STOP_DISTANCE_METERS = 0.3048  # 12 inches = 0.3048m

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
        self.lidar_front_dist_m = 99.0
        self.last_command_sent = None

        # Control Loop Timer (20Hz = 50ms)
        self.timer = self.create_timer(0.05, self.control_loop)

        self.get_logger().info('====================================================')
        self.get_logger().info(' 12-INCH AUTOMATIC PHYSICAL WHEEL CONTROLLER ACTIVE  ')
        self.get_logger().info(f' Threshold: 12 inches ({STOP_DISTANCE_METERS:.2f} meters)')
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
        num = len(ranges)
        if num == 0:
            return

        min_d = 99.0
        for i in range(-15, 15):
            idx = i % num
            r = ranges[idx]
            if 0.05 < r < min_d:
                min_d = r
        self.lidar_front_dist_m = min_d

    def ball_callback(self, msg):
        self.last_ball_time = time.time()
        self.ball_distance_m = msg.x
        self.ball_pixel_offset = msg.y

    def control_loop(self):
        if not rclpy.ok():
            return

        now = time.time()
        has_recent_ball = (now - self.last_ball_time) < 0.8

        closest_object_dist = self.lidar_front_dist_m
        if has_recent_ball and self.ball_distance_m < closest_object_dist:
            closest_object_dist = self.ball_distance_m

        twist = Twist()

        # -----------------------------------------------------------
        # RULE 1: OBJECT WITHIN 12 INCHES (<= 0.30m) -> STOP PHYSICAL WHEELS!
        # -----------------------------------------------------------
        if closest_object_dist <= STOP_DISTANCE_METERS:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.pub_cmd_vel.publish(twist)
            self.send_hardware_motor_cmd('S')
            
            self.get_logger().info(
                f'[STOP] Object detected within 12 inches ({closest_object_dist*39.37:.1f} in / {closest_object_dist:.2f}m)! PHYSICAL WHEELS STOPPED.',
                throttle_duration_sec=0.5
            )

        # -----------------------------------------------------------
        # RULE 2: NO OBJECT WITHIN 12 INCHES (> 0.30m) -> AUTOMATIC MOVE/SPIN!
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
                self.get_logger().info(
                    f'[MOVE] Ball at {self.ball_distance_m*39.37:.1f} in > 12 in. Driving ({cmd}) towards object!',
                    throttle_duration_sec=0.5
                )
            else:
                # No object seen -> Automatically spin physical wheels to search!
                twist.angular.z = 0.65
                self.send_hardware_motor_cmd('R')
                self.pub_cmd_vel.publish(twist)
                self.get_logger().info(
                    f'[AUTO SEARCH] No object within 12 inches ({closest_object_dist:.2f}m). PHYSICAL WHEELS AUTOMATICALLY MOVING/SPINNING...',
                    throttle_duration_sec=0.5
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
