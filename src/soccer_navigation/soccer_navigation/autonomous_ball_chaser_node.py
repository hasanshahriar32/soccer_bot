#!/usr/bin/env python3
"""
====================================================================
  12-INCH PROXIMITY WHEEL CONTROLLER — ROS 2 JAZZY
====================================================================
Description:
    1. Distance Threshold: 12 inches (30.48 cm / 0.305 meters).
    2. When Object / Ball / Obstacle is WITHIN 12 inches (<= 0.30m):
       -> STOP WHEELS IMMEDIATELY (linear.x = 0, angular.z = 0).
    3. When NO object is within 12 inches (> 0.30m):
       -> SPIN / MOVE WHEELS AUTOMATICALLY (search / approach mode).
====================================================================
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import Point, Twist
from sensor_msgs.msg import LaserScan
import time

# 12 inches in meters = 12 * 0.0254 = 0.3048 m
STOP_DISTANCE_METERS = 0.3048

class TwelveInchProximityController(Node):
    def __init__(self):
        super().__init__('twelve_inch_proximity_controller')

        # Subscriptions
        self.sub_ball = self.create_subscription(
            Point, '/ball_position', self.ball_callback, 10)
        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)

        # Publisher for wheel motor commands
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        # State tracking
        self.ball_distance_m = 99.0
        self.ball_pixel_offset = 0.0
        self.last_ball_time = 0.0
        self.lidar_front_dist_m = 99.0

        # Control loop timer (20Hz = every 50ms)
        self.timer = self.create_timer(0.05, self.control_loop)

        self.get_logger().info('====================================================')
        self.get_logger().info(' 12-INCH AUTOMATIC PROXIMITY WHEEL CONTROLLER READY ')
        self.get_logger().info(f' Threshold: 12 inches ({STOP_DISTANCE_METERS:.2f} meters)')
        self.get_logger().info('====================================================')

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
        # RULE 1: OBJECT WITHIN 12 INCHES (<= 0.30m) -> STOP WHEELS!
        # -----------------------------------------------------------
        if closest_object_dist <= STOP_DISTANCE_METERS:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.pub_cmd_vel.publish(twist)
            self.get_logger().info(
                f'[STOP] Object detected within 12 inches ({closest_object_dist*39.37:.1f} in / {closest_object_dist:.2f}m)! WHEELS STOPPED.',
                throttle_duration_sec=0.5
            )

        # -----------------------------------------------------------
        # RULE 2: NO OBJECT WITHIN 12 INCHES (> 0.30m) -> MOVE / SPIN!
        # -----------------------------------------------------------
        else:
            if has_recent_ball:
                angular_z = -0.0035 * self.ball_pixel_offset
                angular_z = max(-1.0, min(1.0, angular_z))
                
                linear_x = 0.25 * (self.ball_distance_m - STOP_DISTANCE_METERS)
                linear_x = max(0.08, min(0.30, linear_x))
                
                twist.linear.x = linear_x
                twist.angular.z = angular_z
                self.get_logger().info(
                    f'[APPROACH] Ball at {self.ball_distance_m*39.37:.1f} in ({self.ball_distance_m:.2f}m) > 12 in. Driving forward (v_x={linear_x:.2f}, w_z={angular_z:.2f})',
                    throttle_duration_sec=0.5
                )
            else:
                twist.linear.x = 0.0
                twist.angular.z = 0.65  # Spin wheels at 0.65 rad/s to scan area
                self.get_logger().info(
                    f'[SEARCH] No object within 12 inches ({closest_object_dist:.2f}m). WHEELS SPINNING TO SEARCH...',
                    throttle_duration_sec=0.5
                )

            self.pub_cmd_vel.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = TwelveInchProximityController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()

if __name__ == '__main__':
    main()
