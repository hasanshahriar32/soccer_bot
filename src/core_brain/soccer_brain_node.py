#!/usr/bin/env python3
"""
soccer_brain_node.py
ROS 2 Core Brain Decision Engine for Soccer Bot.

Subscribes to:
  - /ball_position (geometry_msgs/Point): x = screen_x (0-320), y = screen_y, z = radius
  - /scan (sensor_msgs/LaserScan): Frontal Lidar distance for obstacle safety

Publishes to:
  - /cmd_vel (geometry_msgs/Twist): Linear and Angular velocities sent to motor bridge

States:
  1. SEARCHING: Spin in place to locate the soccer ball
  2. CHASING: Align heading with ball and drive towards it
  3. KICKING: Close range to ball -> push forward at max power
  4. AVOIDING: Lidar front obstacle detected -> rotate away safely
"""

import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, Twist
from sensor_msgs.msg import LaserScan

from rclpy.qos import QoSProfile, QoSReliabilityPolicy

IMAGE_WIDTH = 320
IMAGE_CENTER_X = IMAGE_WIDTH / 2.0  # 160.0
CENTER_TOLERANCE = 40.0             # pixels deadband around center

OBSTACLE_DISTANCE_MIN = 0.25         # meters (25 cm emergency stop)
BALL_KICK_RADIUS_MIN = 60.0          # pixel radius proxy for ball touching front


class SoccerBrainNode(Node):
    def __init__(self):
        super().__init__('soccer_brain_node')

        # --- Subscriptions ---
        self.ball_sub = self.create_subscription(
            Point,
            '/ball_position',
            self.ball_callback,
            10
        )
        
        sensor_qos = QoSProfile(depth=10)
        sensor_qos.reliability = QoSReliabilityPolicy.BEST_EFFORT

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            sensor_qos
        )

        # --- Publisher ---
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # --- State Tracking ---
        self.ball_last_seen = 0.0
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_radius = 0.0
        self.ball_detected = False

        self.front_obstacle = False
        self.front_obstacle_dist = 999.0

        # Control timer running at 10 Hz (0.1s)
        self.timer = self.create_timer(0.1, self.decision_loop)
        self.get_logger().info('Soccer Brain Node initialized & ready.')

    def ball_callback(self, msg: Point):
        self.ball_x = msg.x
        self.ball_y = msg.y
        self.ball_radius = msg.z
        self.ball_last_seen = time.time()
        self.ball_detected = True

    def scan_callback(self, msg: LaserScan):
        # Extract frontal Lidar sector (-30 deg to +30 deg)
        # LaserScan ranges array corresponds to 0..360 deg
        ranges = msg.ranges
        if not ranges:
            return

        num_points = len(ranges)
        # Front 60 deg cone
        front_indices = list(range(0, int(num_points * 30 / 360))) + \
                        list(range(int(num_points * 330 / 360), num_points))

        valid_ranges = [ranges[i] for i in front_indices if msg.range_min < ranges[i] < msg.range_max]

        if valid_ranges:
            min_dist = min(valid_ranges)
            self.front_obstacle_dist = min_dist
            self.front_obstacle = (min_dist < OBSTACLE_DISTANCE_MIN)
        else:
            self.front_obstacle = False

    def decision_loop(self):
        now = time.time()

        # Check if ball detection is fresh (within last 1.0s)
        if (now - self.ball_last_seen) > 1.0:
            self.ball_detected = False

        cmd = Twist()

        # ----------------------------------------------------
        # STATE 1: Emergency Obstacle Avoidance (Highest priority)
        # ----------------------------------------------------
        if self.front_obstacle:
            self.get_logger().warn(f'Obstacle detected ahead ({self.front_obstacle_dist:.2f}m)! Avoiding...')
            cmd.linear.x = 0.0
            cmd.angular.z = 0.15  # Spin left to clear obstacle
            self.cmd_pub.publish(cmd)
            return

        # ----------------------------------------------------
        # STATE 2: Ball Tracked / Chasing
        # ----------------------------------------------------
        if self.ball_detected:
            offset_x = self.ball_x - IMAGE_CENTER_X
            self.get_logger().info(f'Ball Chasing - X:{self.ball_x:.1f} (Offset:{offset_x:.1f}) R:{self.ball_radius:.1f}')

            # Sub-state: Close enough to kick!
            if self.ball_radius >= BALL_KICK_RADIUS_MIN:
                self.get_logger().info('KICKING BALL! Moving forward at full speed.')
                cmd.linear.x = 0.25
                cmd.angular.z = 0.0

            # Ball is off to the right
            elif offset_x > CENTER_TOLERANCE:
                cmd.linear.x = 0.0
                cmd.angular.z = -0.15  # Turn right

            # Ball is off to the left
            elif offset_x < -CENTER_TOLERANCE:
                cmd.linear.x = 0.0
                cmd.angular.z = 0.15   # Turn left

            # Ball is centered in front -> Drive straight forward!
            else:
                cmd.linear.x = 0.2
                cmd.angular.z = 0.0

        # ----------------------------------------------------
        # STATE 3: Searching for Ball (Spin in place)
        # ----------------------------------------------------
        else:
            self.get_logger().info('Searching for ball... Spinning in place.')
            cmd.linear.x = 0.0
            cmd.angular.z = 0.15  # Spin searching

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = SoccerBrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())  # Stop on exit
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
