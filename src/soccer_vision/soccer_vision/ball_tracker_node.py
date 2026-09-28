#!/usr/bin/env python3
"""
====================================================================
  CAMERA-LIDAR SYNCHRONIZED SOCCER BALL TRACKER — ROS 2 JAZZY
====================================================================
Description:
    1. Subscribes to /image_raw (Camera) and /scan (LiDAR).
    2. Detects colored soccer ball in visual space (pixel cx, cy, radius).
    3. Calculates optical bearing angle θ = -atan2(cx - W/2, fx).
    4. Synchronizes with LiDAR /scan:
       - Samples laser rays within an angular window around θ.
       - Extracts exact physical ground-truth distance r to ball front edge.
       - Falls back gracefully to visual size estimation if laser misses.
    5. Publishes:
       - /ball_position (geometry_msgs/Point):
           x: forward distance in meters (X in base_link)
           y: lateral offset in meters (Y in base_link, + left, - right)
           z: Euclidean distance in meters (r)
       - /ball_marker   (visualization_msgs/MarkerArray):
           3D Sphere, Tracking Ray, and floating Text HUD above ball.
====================================================================
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker, MarkerArray
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np
import math
import threading
import time

# --------------- Physical & Optical Constants ---------------
KNOWN_BALL_DIAMETER_M = 0.065   # Standard ball diameter (~6.5 cm)
CAMERA_FOV_H = math.radians(62.0)  # Raspberry Pi Camera horizontal FOV (62 deg)

# --------------- Detection Tuning ---------------
MIN_CONTOUR_AREA = 120          # Minimum blob area in pixels²
MIN_RADIUS_PX = 6               # Minimum enclosing circle radius
MIN_CIRCULARITY = 0.45          # 4π·area/perimeter² threshold
EMA_ALPHA = 0.40                # Exponential Moving Average smoothing
BALL_LOST_GRACE_SEC = 1.0       # Retain tracking for 1.0s after occlusion


class BallTrackerNode(Node):
    def __init__(self):
        super().__init__('ball_tracker')

        self.bridge = CvBridge()
        self.scan_lock = threading.Lock()
        self.latest_scan = None
        self.latest_scan_time = 0.0

        # Subscriptions
        self.sub_image = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)

        # Publishers
        self.pub_position = self.create_publisher(Point, '/ball_position', 10)
        self.pub_markers = self.create_publisher(MarkerArray, '/ball_marker', 10)

        # --------------- HSV Color Ranges ---------------
        # Supports yellow tennis balls, orange soccer balls, red, green, blue
        self.hsv_ranges = [
            # Yellow / Tennis ball (HSV ~ 22-42)
            (np.array([20, 70, 70]),   np.array([45, 255, 255])),
            # Orange ball (HSV ~ 5-22)
            (np.array([5, 90, 90]),    np.array([22, 255, 255])),
            # Red ball (wraps around hue 0 and 180)
            (np.array([0, 90, 80]),    np.array([8, 255, 255])),
            (np.array([168, 90, 80]),  np.array([180, 255, 255])),
            # Green ball
            (np.array([45, 70, 70]),   np.array([85, 255, 255])),
            # Blue ball
            (np.array([90, 80, 80]),   np.array([130, 255, 255])),
        ]

        # --------------- Tracking State ---------------
        self.smooth_x = 0.0
        self.smooth_y = 0.0
        self.smooth_r = 0.0
        self.last_detection_time = 0.0
        self.has_detection = False

        self.get_logger().info('===========================================================')
        self.get_logger().info(' ⚽ CAMERA-LIDAR SYNCHRONIZED BALL TRACKER ACTIVE')
        self.get_logger().info(' Optical Bearing + LaserScan Ground-Truth Distance Fusion')
        self.get_logger().info(' Publishing: /ball_position & /ball_marker (MarkerArray)')
        self.get_logger().info('===========================================================')

    def scan_callback(self, msg: LaserScan):
        with self.scan_lock:
            self.latest_scan = msg
            self.latest_scan_time = time.time()

    def sync_lidar_distance(self, bearing_rad: float):
        """Finds closest LiDAR range within an angular cone around bearing_rad."""
        with self.scan_lock:
            scan = self.latest_scan
            scan_time = self.latest_scan_time

        if scan is None or (time.time() - scan_time) > 1.2:
            return None, "NO_LIDAR"

        # Cone window: +/- 0.12 rad (~7 degrees)
        half_window = 0.12
        min_angle = bearing_rad - half_window
        max_angle = bearing_rad + half_window

        valid_ranges = []
        for i, r in enumerate(scan.ranges):
            ray_angle = scan.angle_min + i * scan.angle_increment
            # Normalize to [-pi, pi]
            ray_angle = math.atan2(math.sin(ray_angle), math.cos(ray_angle))

            if min_angle <= ray_angle <= max_angle:
                if scan.range_min <= r <= scan.range_max and not math.isnan(r) and not math.isinf(r):
                    if 0.08 <= r <= 8.0:
                        valid_ranges.append(r)

        if valid_ranges:
            r_front = min(valid_ranges)
            # Add ball radius to get distance to center of ball
            r_center = r_front + (KNOWN_BALL_DIAMETER_M / 2.0)
            return r_center, "LIDAR_SYNC"

        return None, "NO_RETURN"

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CV Bridge Error: {e}")
            return

        now = time.time()
        img_h, img_w = frame.shape[:2]
        focal_px = (img_w / 2.0) / math.tan(CAMERA_FOV_H / 2.0)

        detection = self.detect_ball(frame)

        if detection is not None:
            cx, cy, radius = detection

            # Temporal EMA smoothing on pixel coordinates
            if self.has_detection:
                self.smooth_x = EMA_ALPHA * cx + (1.0 - EMA_ALPHA) * self.smooth_x
                self.smooth_y = EMA_ALPHA * cy + (1.0 - EMA_ALPHA) * self.smooth_y
                self.smooth_r = EMA_ALPHA * radius + (1.0 - EMA_ALPHA) * self.smooth_r
            else:
                self.smooth_x = float(cx)
                self.smooth_y = float(cy)
                self.smooth_r = float(radius)

            self.last_detection_time = now
            self.has_detection = True

            # Bearing angle in base_link (Forward = 0, Left = +θ, Right = -θ)
            pixel_offset = (img_w / 2.0) - self.smooth_x
            bearing_rad = math.atan2(pixel_offset, focal_px)

            # Fuse with LiDAR /scan
            lidar_dist, mode = self.sync_lidar_distance(bearing_rad)
            if lidar_dist is not None:
                distance_m = lidar_dist
            else:
                # Fallback to monocular optical distance estimation
                distance_m = (KNOWN_BALL_DIAMETER_M * focal_px) / (2.0 * max(1.0, self.smooth_r))
                distance_m = min(max(distance_m, 0.12), 6.0)
                mode = "CAMERA_EST"

            # 3D Cartesian coordinates relative to robot base_link
            ball_x = distance_m * math.cos(bearing_rad)
            ball_y = distance_m * math.sin(bearing_rad)

            # Publish Point: x=forward(m), y=lateral(m), z=total_distance(m)
            pos_msg = Point()
            pos_msg.x = float(ball_x)
            pos_msg.y = float(ball_y)
            pos_msg.z = float(distance_m)
            self.pub_position.publish(pos_msg)

            # Publish 3D Markers to RViz
            self.publish_rviz_markers(ball_x, ball_y, distance_m, bearing_rad, mode, msg.header.stamp)

        elif self.has_detection and (now - self.last_detection_time) >= BALL_LOST_GRACE_SEC:
            # Ball lost
            self.has_detection = False
            lost_msg = Point(x=-1.0, y=-1.0, z=-1.0)
            self.pub_position.publish(lost_msg)
            self.delete_rviz_markers(msg.header.stamp)

    def detect_ball(self, frame):
        """Detect the best circular colored ball blob in the frame."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Combine all tuned color masks
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in self.hsv_ranges:
            combined_mask = cv2.bitwise_or(
                combined_mask, cv2.inRange(hsv, lower, upper))

        # Morphological noise removal
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

            circularity = (4.0 * math.pi * area) / (perimeter * perimeter)
            if circularity < MIN_CIRCULARITY:
                continue

            ((cx, cy), radius) = cv2.minEnclosingCircle(c)
            if radius < MIN_RADIUS_PX:
                continue

            score = area * circularity
            if score > best_score:
                best_score = score
                best_result = (int(cx), int(cy), radius)

        return best_result

    def publish_rviz_markers(self, ball_x, ball_y, dist_m, bearing_rad, mode, stamp):
        """Publishes 3D Sphere, Floating Text HUD, and Ray to /ball_marker."""
        ma = MarkerArray()

        # 1. 3D Ball Sphere
        m_sphere = Marker()
        m_sphere.header.stamp = stamp
        m_sphere.header.frame_id = 'base_link'
        m_sphere.ns = 'ball_tracker'
        m_sphere.id = 0
        m_sphere.type = Marker.SPHERE
        m_sphere.action = Marker.ADD
        m_sphere.pose.position.x = ball_x
        m_sphere.pose.position.y = ball_y
        m_sphere.pose.position.z = 0.033
        m_sphere.pose.orientation.w = 1.0
        m_sphere.scale.x = KNOWN_BALL_DIAMETER_M * 1.5
        m_sphere.scale.y = KNOWN_BALL_DIAMETER_M * 1.5
        m_sphere.scale.z = KNOWN_BALL_DIAMETER_M * 1.5
        m_sphere.color.r = 1.0
        m_sphere.color.g = 0.85
        m_sphere.color.b = 0.0
        m_sphere.color.a = 0.95
        m_sphere.lifetime.sec = 1
        ma.markers.append(m_sphere)

        # 2. Floating Text HUD above ball
        bearing_deg = math.degrees(bearing_rad)
        m_text = Marker()
        m_text.header.stamp = stamp
        m_text.header.frame_id = 'base_link'
        m_text.ns = 'ball_tracker'
        m_text.id = 1
        m_text.type = Marker.TEXT_VIEW_FACING
        m_text.action = Marker.ADD
        m_text.pose.position.x = ball_x
        m_text.pose.position.y = ball_y
        m_text.pose.position.z = 0.16
        m_text.scale.z = 0.09  # Text height
        m_text.text = f"⚽ BALL: {dist_m:.2f}m [{mode}] θ={bearing_deg:+.1f}°"
        m_text.color.r = 0.0
        m_text.color.g = 1.0
        m_text.color.b = 0.4
        m_text.color.a = 1.0
        m_text.lifetime.sec = 1
        ma.markers.append(m_text)

        # 3. Ray from Robot Origin to Ball
        m_ray = Marker()
        m_ray.header.stamp = stamp
        m_ray.header.frame_id = 'base_link'
        m_ray.ns = 'ball_tracker'
        m_ray.id = 2
        m_ray.type = Marker.LINE_STRIP
        m_ray.action = Marker.ADD
        m_ray.scale.x = 0.02  # Line width
        m_ray.color.r = 0.0
        m_ray.color.g = 0.9
        m_ray.color.b = 1.0
        m_ray.color.a = 0.75
        p0 = Point(x=0.0, y=0.0, z=0.05)
        p1 = Point(x=ball_x, y=ball_y, z=0.033)
        m_ray.points = [p0, p1]
        m_ray.lifetime.sec = 1
        ma.markers.append(m_ray)

        self.pub_markers.publish(ma)

    def delete_rviz_markers(self, stamp):
        ma = MarkerArray()
        for idx in [0, 1, 2]:
            m = Marker()
            m.header.stamp = stamp
            m.header.frame_id = 'base_link'
            m.ns = 'ball_tracker'
            m.id = idx
            m.action = Marker.DELETE
            ma.markers.append(m)
        self.pub_markers.publish(ma)


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
