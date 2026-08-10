#!/usr/bin/env python3
"""
====================================================================
       SOCCER BOT BRAIN — SMOOTH PD BALL CHASE CONTROLLER
====================================================================
Description:
    Central decision engine that fuses ball detection with Lidar
    obstacle avoidance to produce smooth, proportional /cmd_vel
    commands for autonomous ball chasing.

State Machine:
    1. CHASING    — Ball detected: PD steering + distance-ramped speed
    2. COASTING   — Ball briefly lost (<0.8s): continue last trajectory
    3. SEARCHING  — Ball fully lost: spin toward last-known direction
    4. AVOIDING   — Frontal obstacle < 25cm: rotate away safely
    5. KICKING    — Ball within kick range: full-speed forward push

Subscribes:
    /ball_position  (geometry_msgs/Point) — x=px, y=px, z=radius
    /scan           (sensor_msgs/LaserScan) — 360° Lidar for obstacles

Publishes:
    /cmd_vel        (geometry_msgs/Twist) — Linear + Angular velocities
====================================================================
"""

import time
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, Twist
from sensor_msgs.msg import LaserScan
from rclpy.qos import QoSProfile, QoSReliabilityPolicy

# --------------- Camera & Geometry ---------------
IMAGE_WIDTH = 320
IMAGE_CENTER_X = IMAGE_WIDTH / 2.0        # 160.0
CENTER_DEADZONE = 25.0                     # Pixels — no steering correction needed

# --------------- PD Steering Gains ---------------
KP_STEER = 0.006                           # Proportional gain (deg/px → rad/s)
KD_STEER = 0.002                           # Derivative gain (smooths oscillation)

# --------------- Speed Control ---------------
MAX_FORWARD_SPEED = 0.22                   # m/s max approach speed
MIN_FORWARD_SPEED = 0.08                   # m/s minimum creep speed
SEARCH_SPIN_SPEED = 0.18                   # rad/s spin-in-place search speed

# --------------- Ball Range Thresholds ---------------
KICK_RADIUS_PX = 100.0                     # Ball radius (px) that means "touching"
KICK_SPEED = 0.28                          # Full-speed forward kick push

# --------------- Obstacle Avoidance ---------------
OBSTACLE_EMERGENCY_M = 0.22               # meters — emergency stop
OBSTACLE_CONE_DEG = 35.0                  # Half-angle of front cone

# --------------- Timing ---------------
BALL_LOST_GRACE_SEC = 0.8                  # Coast for 0.8s before searching
CONTROL_HZ = 15.0                         # Decision loop frequency


class SoccerBrainNode(Node):
    def __init__(self):
        super().__init__('soccer_brain_node')

        # --- Subscriptions ---
        self.sub_ball = self.create_subscription(
            Point, '/ball_position', self.ball_callback, 10)

        sensor_qos = QoSProfile(depth=10)
        sensor_qos.reliability = QoSReliabilityPolicy.BEST_EFFORT
        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, sensor_qos)

        # --- Publisher ---
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)

        # --- Ball Tracking State ---
        self.ball_x = -1.0
        self.ball_y = -1.0
        self.ball_radius = 0.0
        self.ball_detected = False
        self.ball_last_seen = 0.0
        self.last_ball_direction = 1.0     # +1 = ball was last seen left, -1 = right

        # PD controller state
        self.prev_error_x = 0.0

        # Coast state (last good velocity)
        self.coast_linear = 0.0
        self.coast_angular = 0.0

        # --- Obstacle State ---
        self.front_blocked = False
        self.front_min_dist = 999.0
        self.front_closest_angle = 0.0
        self.ball_angle_rad = 0.0          # Current ball heading for obstacle filtering

        # --- Control Timer ---
        self.timer = self.create_timer(1.0 / CONTROL_HZ, self.decision_loop)
        self.get_logger().info('Soccer Brain (Smooth PD Chase) initialized.')

    # ======================== CALLBACKS ========================

    def ball_callback(self, msg: Point):
        if msg.x < 0:
            # Ball lost signal from tracker
            self.ball_detected = False
            return

        self.ball_x = msg.x
        self.ball_y = msg.y
        self.ball_radius = msg.z
        self.ball_detected = True
        self.ball_last_seen = time.time()

        # Remember which side the ball was last seen on
        if self.ball_x > IMAGE_CENTER_X + 10:
            self.last_ball_direction = -1.0  # Ball is right → spin right to find
        elif self.ball_x < IMAGE_CENTER_X - 10:
            self.last_ball_direction = 1.0   # Ball is left → spin left to find

        # Ball heading angle for obstacle filtering
        offset_px = self.ball_x - IMAGE_CENTER_X
        focal_px = IMAGE_WIDTH / (2.0 * math.tan(math.radians(31.0)))
        self.ball_angle_rad = math.atan2(offset_px, focal_px)

    def scan_callback(self, msg: LaserScan):
        if not msg.ranges:
            return

        n = len(msg.ranges)
        front_cone_idx = int(n * OBSTACLE_CONE_DEG / 360.0)

        # Front cone indices (wrapping around 0°)
        indices = list(range(0, front_cone_idx)) + list(range(n - front_cone_idx, n))

        min_dist = 999.0
        closest_angle = 0.0

        for i in indices:
            r = msg.ranges[i]
            if not math.isfinite(r) or r < 0.05:
                continue

            angle = msg.angle_min + i * msg.angle_increment

            # Skip readings near the ball's known angle (don't avoid the ball itself)
            if self.ball_detected and abs(angle - self.ball_angle_rad) < math.radians(15.0):
                continue

            if r < min_dist:
                min_dist = r
                closest_angle = angle

        self.front_min_dist = min_dist
        self.front_blocked = (min_dist < OBSTACLE_EMERGENCY_M)
        self.front_closest_angle = closest_angle

    # ======================== DECISION LOOP ========================

    def decision_loop(self):
        now = time.time()
        time_since_ball = now - self.ball_last_seen if self.ball_last_seen > 0 else 999.0
        cmd = Twist()

        # ---- STATE: OBSTACLE AVOIDANCE (Highest Priority) ----
        if self.front_blocked and not self.ball_detected:
            cmd.linear.x = 0.0
            if self.front_closest_angle > 0:
                cmd.angular.z = -SEARCH_SPIN_SPEED  # Obstacle on left → turn right
            else:
                cmd.angular.z = SEARCH_SPIN_SPEED   # Obstacle on right → turn left
            self.pub_cmd.publish(cmd)
            return

        # ---- STATE: CHASING / KICKING (Ball detected) ----
        if self.ball_detected and time_since_ball < 0.3:
            error_x = IMAGE_CENTER_X - self.ball_x

            # PD steering controller
            d_error = error_x - self.prev_error_x
            self.prev_error_x = error_x

            if abs(error_x) > CENTER_DEADZONE:
                cmd.angular.z = KP_STEER * error_x + KD_STEER * d_error
                cmd.angular.z = max(-0.5, min(0.5, cmd.angular.z))  # Clamp
            else:
                cmd.angular.z = 0.0

            # Sub-state: KICK (ball very close)
            if self.ball_radius >= KICK_RADIUS_PX:
                cmd.linear.x = KICK_SPEED
                cmd.angular.z *= 0.3  # Reduce steering during kick push

            # Sub-state: APPROACH (distance-proportional speed ramp)
            else:
                approach_ratio = self.ball_radius / KICK_RADIUS_PX
                speed = MAX_FORWARD_SPEED * (1.0 - approach_ratio * 0.7)
                cmd.linear.x = max(MIN_FORWARD_SPEED, speed)

                # Reduce forward speed during heavy steering
                steer_penalty = 1.0 - min(abs(cmd.angular.z) / 0.4, 0.6)
                cmd.linear.x *= steer_penalty

            # Save for coast phase
            self.coast_linear = cmd.linear.x
            self.coast_angular = cmd.angular.z

            self.pub_cmd.publish(cmd)
            return

        # ---- STATE: COASTING (Ball briefly lost, continue last trajectory) ----
        if time_since_ball < BALL_LOST_GRACE_SEC:
            cmd.linear.x = self.coast_linear * 0.5   # Half speed coast
            cmd.angular.z = self.coast_angular * 0.3  # Gentle drift
            self.pub_cmd.publish(cmd)
            return

        # ---- STATE: SEARCHING (Ball fully lost) ----
        cmd.linear.x = 0.0
        cmd.angular.z = self.last_ball_direction * SEARCH_SPIN_SPEED
        self.pub_cmd.publish(cmd)

    # ======================== CLEANUP ========================

    def destroy_node(self):
        self.pub_cmd.publish(Twist())  # Stop motors on exit
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SoccerBrainNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.pub_cmd.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
