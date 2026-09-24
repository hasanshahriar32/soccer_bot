#!/usr/bin/env python3
"""
====================================================================
  12-INCH PROXIMITY & ACTIVE FORWARD DRIVE CONTROLLER — ROS 2 JAZZY
====================================================================
Description:
    Connected directly to Raspberry Pi Motor Server (Port 9000).
    
    1. Threshold: 12 inches (30.48 cm / 0.3048 m).
    2. WHEN OBJECT DETECTED > 12 INCHES:
       -> Aligns heading and DRIVES FORWARD actively (SET:190,190).
    3. WHEN OBJECT DETECTED <= 12 INCHES:
       -> STOPS PHYSICAL WHEELS INSTANTLY (SET:0,0 / 'S').
    4. WHEN NO OBJECT SEEN:
       -> SPINS PHYSICAL WHEELS TO SEARCH (SET:170,-170).
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

class ActiveDrive12InchController(Node):
    def __init__(self):
        super().__init__('active_drive_12inch_controller')

        self.pi_ip = '10.72.30.146'
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
        self.get_logger().info(' 12-INCH PROXIMITY & ACTIVE FORWARD DRIVE READY     ')
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

    def send_motor_pwm(self, left_pwm, right_pwm, raw_cmd):
        cmd_str = f"SET:{left_pwm},{right_pwm}\n"
        if cmd_str == self.last_command_sent:
            return
        self.last_command_sent = cmd_str
        
        with self.sock_lock:
            if self.motor_sock:
                try:
                    payload = f"3\n{raw_cmd}\n{cmd_str}".encode()
                    self.motor_sock.sendall(payload)
                except:
                    self.motor_sock = None

    def scan_callback(self, msg):
        ranges = msg.ranges
        if len(ranges) == 0:
            return

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
            self.send_motor_pwm(0, 0, 'S')
            
            dist_inches = closest_object_dist * 39.3701
            self.get_logger().info(
                f'[STOP] 🛑 OBJECT AT {dist_inches:.1f} in (<= 12 in)! PHYSICAL WHEELS STOPPED.',
                throttle_duration_sec=0.4
            )

        # -----------------------------------------------------------
        # RULE 2: OBJECT DETECTED > 12 INCHES -> DRIVE FORWARD TO OBJECT!
        # -----------------------------------------------------------
        else:
            if has_recent_ball:
                dist_inches = self.ball_distance_m * 39.3701
                
                # Check alignment with object
                if self.ball_pixel_offset < -35:
                    # Object to the left -> Turn left
                    self.send_motor_pwm(-170, 170, 'L')
                    twist.angular.z = 0.6
                    action = f"TURNING LEFT towards object ({dist_inches:.1f} in)"
                elif self.ball_pixel_offset > 35:
                    # Object to the right -> Turn right
                    self.send_motor_pwm(170, -170, 'R')
                    twist.angular.z = -0.6
                    action = f"TURNING RIGHT towards object ({dist_inches:.1f} in)"
                else:
                    # Centered -> DRIVE FORWARD TO OBJECT!
                    self.send_motor_pwm(195, 195, 'F')
                    twist.linear.x = 0.28
                    action = f"DRIVING FORWARD to object ({dist_inches:.1f} in)"

                self.pub_cmd_vel.publish(twist)
                self.get_logger().info(
                    f'[ACTIVE CHASE] 🎯 {action}!',
                    throttle_duration_sec=0.4
                )
            else:
                # No object seen -> Spin wheels to search!
                twist.angular.z = 0.65
                self.send_motor_pwm(170, -170, 'R')
                self.pub_cmd_vel.publish(twist)
                self.get_logger().info(
                    f'[AUTO SEARCH] 🔄 Searching for object > 12 in. WHEELS SPINNING...',
                    throttle_duration_sec=0.4
                )

def main(args=None):
    rclpy.init(args=args)
    node = ActiveDrive12InchController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.send_motor_pwm(0, 0, 'S')
        node.destroy_node()

if __name__ == '__main__':
    main()
