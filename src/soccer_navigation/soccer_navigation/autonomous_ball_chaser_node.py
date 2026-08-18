#!/usr/bin/env python3
"""
====================================================================
     AUTONOMOUS BALL CHASER & STEERING CONTROL NODE — ROS 2 JAZZY
====================================================================
Description:
    Subscribes to /ball_position (from ball_tracker_node) and /scan.
    Computes proportional steering (angular.z) and forward drive (linear.x)
    to autonomously track, align, and approach detected soccer balls.
====================================================================
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import Point, Twist
from sensor_msgs.msg import LaserScan
import time

class AutonomousBallChaser(Node):
    def __init__(self):
        super().__init__('autonomous_ball_chaser')

        # Subscriptions
        self.sub_ball = self.create_subscription(
            Point, '/ball_position', self.ball_callback, 10)
        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)

        # Publisher for standard ROS velocity commands
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        # Control Parameters
        self.target_dist_m = 0.20        # Stop 20 cm from ball
        self.kp_linear = 0.45            # Forward speed gain
        self.kp_angular = 0.0035         # Steering gain per pixel offset
        self.max_linear_speed = 0.35     # Max forward speed m/s
        self.max_angular_speed = 1.2     # Max turning speed rad/s

        # Safety State
        self.obstacle_blocked = False
        self.last_ball_time = 0.0

        self.get_logger().info('====================================================')
        self.get_logger().info(' AUTONOMOUS BALL CHASER & STEERING CONTROLLER ACTIVE')
        self.get_logger().info('====================================================')

    def scan_callback(self, msg):
        ranges = msg.ranges
        num_readings = len(ranges)
        if num_readings == 0:
            return

        front_min_dist = 99.0
        for i in range(-15, 15):
            idx = i % num_readings
            r = ranges[idx]
            if 0.05 < r < front_min_dist:
                front_min_dist = r

        if front_min_dist < 0.15: # 15 cm safety buffer
            if not self.obstacle_blocked:
                self.get_logger().warn(f'SAFETY OBSTACLE DETECTED at {front_min_dist:.2f}m! Pausing drive.')
            self.obstacle_blocked = True
        else:
            self.obstacle_blocked = False

    def ball_callback(self, msg):
        self.last_ball_time = time.time()

        dist_m = msg.x
        pixel_offset_x = msg.y

        twist = Twist()

        if self.obstacle_blocked:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.pub_cmd_vel.publish(twist)
            return

        # 1. Proportional Angular Steering Control
        angular_z = -self.kp_angular * pixel_offset_x
        angular_z = max(-self.max_angular_speed, min(self.max_angular_speed, angular_z))

        # 2. Proportional Linear Forward Drive Control
        dist_error = dist_m - self.target_dist_m
        if abs(pixel_offset_x) < 45 and dist_error > 0.02:
            linear_x = self.kp_linear * dist_error
            linear_x = max(0.0, min(self.max_linear_speed, linear_x))
        else:
            linear_x = 0.0

        twist.linear.x = linear_x
        twist.angular.z = angular_z
        self.pub_cmd_vel.publish(twist)

        self.get_logger().info(
            f'Ball Track -> Dist: {dist_m:.2f}m | Offset: {pixel_offset_x:.0f}px | Cmd -> v_x: {linear_x:.2f} m/s, w_z: {angular_z:.2f} rad/s',
            throttle_duration_sec=0.5
        )

def main(args=None):
    rclpy.init(args=args)
    node = AutonomousBallChaser()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
