#!/usr/bin/env python3
"""
====================================================================
          SOCCER BALL TRACKER NODE (IMPROVED) — ROS 2 JAZZY
====================================================================
Description:
    Detects colored soccer balls via HSV color filtering with strict
    circularity validation, temporal EMA smoothing, ball-lost prediction,
    and publishes a real-time 3D RViz Marker sphere on the map.

Subscribes: /image_raw (sensor_msgs/Image) — 320x240 @ 10 FPS
Publishes:
    /ball_position   (geometry_msgs/Point)  — x=px, y=px, z=radius
    /ball_marker     (visualization_msgs/Marker) — 3D sphere on map
====================================================================
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np
import math
import time

# --------------- Camera Constants ---------------
IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
CAMERA_FOV_H = math.radians(62.0)  # Pi Camera V2 horizontal FOV
KNOWN_BALL_DIAMETER_M = 0.065       # Standard soccer ball ~6.5 cm diameter

# --------------- Detection Tuning ---------------
MIN_CONTOUR_AREA = 200              # Minimum blob area in pixels²
MIN_RADIUS_PX = 8                   # Minimum enclosing circle radius
MIN_CIRCULARITY = 0.55              # 4π·area/perimeter² threshold
EMA_ALPHA = 0.35                    # Exponential Moving Average smoothing
BALL_LOST_GRACE_SEC = 0.8           # Continue predicting for 0.8s after lost


class BallTrackerNode(Node):
    def __init__(self):
        super().__init__('ball_tracker')

        self.bridge = CvBridge()

        # Subscriptions
        self.sub_image = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)

        # Publishers
        self.pub_position = self.create_publisher(Point, '/ball_position', 10)
        self.pub_marker = self.create_publisher(Marker, '/ball_marker', 10)

        # --------------- HSV Color Ranges ---------------
        # Tuned for common indoor-lit colored balls
        self.hsv_ranges = [
            # Orange ball (most common soccer ball)
            (np.array([5, 100, 100]),  np.array([25, 255, 255])),
            # Red ball (wraps around hue=0)
            (np.array([0, 100, 100]),  np.array([5, 255, 255])),
            (np.array([170, 100, 100]), np.array([180, 255, 255])),
            # Yellow ball
            (np.array([25, 100, 100]), np.array([40, 255, 255])),
            # Green ball
            (np.array([40, 80, 80]),   np.array([80, 255, 255])),
            # Blue ball
            (np.array([90, 80, 80]),   np.array([130, 255, 255])),
        ]

        # --------------- Tracking State ---------------
        self.smooth_x = 0.0
        self.smooth_y = 0.0
        self.smooth_r = 0.0
        self.last_detection_time = 0.0
        self.has_detection = False

        # Velocity estimation for prediction
        self.prev_x = 0.0
        self.prev_y = 0.0
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.prev_time = 0.0

        self.get_logger().info(
            'Ball Tracker active (circularity filter + EMA smoothing + RViz marker)')

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CV Bridge Error: {e}")
            return

        now = time.time()
        detection = self.detect_ball(frame)

        if detection is not None:
            cx, cy, radius = detection

            # EMA smoothing
            if self.has_detection:
                self.smooth_x = EMA_ALPHA * cx + (1.0 - EMA_ALPHA) * self.smooth_x
                self.smooth_y = EMA_ALPHA * cy + (1.0 - EMA_ALPHA) * self.smooth_y
                self.smooth_r = EMA_ALPHA * radius + (1.0 - EMA_ALPHA) * self.smooth_r
            else:
                self.smooth_x = float(cx)
                self.smooth_y = float(cy)
                self.smooth_r = float(radius)

            # Update velocity estimate
            dt = now - self.prev_time if self.prev_time > 0 else 0.1
            if dt > 0 and self.has_detection:
                self.vel_x = (self.smooth_x - self.prev_x) / dt
                self.vel_y = (self.smooth_y - self.prev_y) / dt

            self.prev_x = self.smooth_x
            self.prev_y = self.smooth_y
            self.prev_time = now
            self.last_detection_time = now
            self.has_detection = True

            self.publish_position(self.smooth_x, self.smooth_y, self.smooth_r)
            self.publish_rviz_marker(self.smooth_x, self.smooth_y, self.smooth_r, msg.header.stamp)

        elif self.has_detection and (now - self.last_detection_time) < BALL_LOST_GRACE_SEC:
            # Ball briefly lost — predict position from last velocity
            dt = now - self.prev_time
            pred_x = self.smooth_x + self.vel_x * dt
            pred_y = self.smooth_y + self.vel_y * dt

            self.publish_position(pred_x, pred_y, self.smooth_r)
            self.publish_rviz_marker(pred_x, pred_y, self.smooth_r, msg.header.stamp)

        elif self.has_detection and (now - self.last_detection_time) >= BALL_LOST_GRACE_SEC:
            # Grace period expired — ball truly lost
            self.has_detection = False
            lost_msg = Point()
            lost_msg.x = -1.0
            lost_msg.y = -1.0
            lost_msg.z = 0.0
            self.pub_position.publish(lost_msg)
            self.delete_rviz_marker(msg.header.stamp)

    def detect_ball(self, frame):
        """Detect the best circular colored blob in the frame."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Combine all color masks
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in self.hsv_ranges:
            combined_mask = cv2.bitwise_or(
                combined_mask, cv2.inRange(hsv, lower, upper))

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(
            combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_score = 0.0
        best_result = None

        for c in contours:
            area = cv2.contourArea(c)
            if area < MIN_CONTOUR_AREA:
                continue

            perimeter = cv2.arcLength(c, True)
            if perimeter < 1.0:
                continue

            # Circularity check: perfect circle = 1.0
            circularity = (4.0 * math.pi * area) / (perimeter * perimeter)
            if circularity < MIN_CIRCULARITY:
                continue

            ((cx, cy), radius) = cv2.minEnclosingCircle(c)
            if radius < MIN_RADIUS_PX:
                continue

            # Score by area × circularity (prefer large round blobs)
            score = area * circularity
            if score > best_score:
                best_score = score
                best_result = (int(cx), int(cy), radius)

        return best_result

    def publish_position(self, x, y, radius):
        msg = Point()
        msg.x = float(x)
        msg.y = float(y)
        msg.z = float(radius)
        self.pub_position.publish(msg)

    def publish_rviz_marker(self, px, py, radius_px, stamp):
        """Publish a 3D sphere marker on the RViz map at estimated ball position."""
        # Estimate distance from apparent radius
        if radius_px < 1.0:
            return
        focal_px = IMAGE_WIDTH / (2.0 * math.tan(CAMERA_FOV_H / 2.0))
        distance_m = (KNOWN_BALL_DIAMETER_M * focal_px) / (2.0 * radius_px)
        distance_m = min(distance_m, 5.0)  # Clamp max

        # Estimate horizontal angle from pixel offset
        offset_px = px - (IMAGE_WIDTH / 2.0)
        angle_rad = math.atan2(offset_px, focal_px)

        # Convert to 3D position in base_link frame
        ball_x = distance_m * math.cos(angle_rad)
        ball_y = -distance_m * math.sin(angle_rad)

        marker = Marker()
        marker.header.stamp = stamp
        marker.header.frame_id = 'base_link'
        marker.ns = 'ball'
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.position.x = ball_x
        marker.pose.position.y = ball_y
        marker.pose.position.z = 0.033  # Ball resting on ground
        marker.pose.orientation.w = 1.0
        marker.scale.x = KNOWN_BALL_DIAMETER_M
        marker.scale.y = KNOWN_BALL_DIAMETER_M
        marker.scale.z = KNOWN_BALL_DIAMETER_M
        marker.color.r = 1.0
        marker.color.g = 0.4
        marker.color.b = 0.0
        marker.color.a = 0.9
        marker.lifetime.sec = 1
        self.pub_marker.publish(marker)

    def delete_rviz_marker(self, stamp):
        marker = Marker()
        marker.header.stamp = stamp
        marker.header.frame_id = 'base_link'
        marker.ns = 'ball'
        marker.id = 0
        marker.action = Marker.DELETE
        self.pub_marker.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    node = BallTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
