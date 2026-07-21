#!/usr/bin/env python3
"""
ball_tracker_node.py
Universal Multi-Color & Shape-Adaptive Soccer Ball Tracker.

Tracks colored balls (Orange, Red, Yellow, Green, Blue, Pink) as well as
traditional black-and-white soccer balls using circularity shape detection.

Subscribes to: /image_raw (sensor_msgs/Image)
Publishes to:  /ball_position (geometry_msgs/Point): x, y, z=radius
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np


class BallTrackerNode(Node):
    def __init__(self):
        super().__init__('ball_tracker')

        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10
        )
        self.publisher_ = self.create_publisher(Point, '/ball_position', 10)
        self.get_logger().info('Universal Ball Tracker active. Subscribed to /image_raw')

        # Robust HSV ranges (low saturation thresholds for indoor lighting)
        self.hsv_ranges = [
            (np.array([ 0, 30, 30]), np.array([25, 255, 255])),   # Orange / Yellow
            (np.array([160, 30, 30]), np.array([180, 255, 255])), # Red / Pink
            (np.array([ 30, 30, 30]), np.array([85, 255, 255])),  # Green
            (np.array([ 85, 30, 30]), np.array([140, 255, 255])), # Blue / Cyan
        ]

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CV Bridge Error: {e}")
            return

        center, radius = self.process_frame(cv_image)

        if center is not None:
            ball_msg = Point()
            ball_msg.x = float(center[0])
            ball_msg.y = float(center[1])
            ball_msg.z = float(radius)
            self.publisher_.publish(ball_msg)
            self.get_logger().info(f"⚽ BALL DETECTED -> Center X: {center[0]}, Y: {center[1]}, Radius: {radius:.1f}px")

    def process_frame(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 1. Color Masking (Combined HSV)
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in self.hsv_ranges:
            m = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, m)

        combined_mask = cv2.erode(combined_mask, None, iterations=2)
        combined_mask = cv2.dilate(combined_mask, None, iterations=2)

        contours, _ = cv2.findContours(combined_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            if cv2.contourArea(c) > 100:
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                if radius > 6:
                    return (int(x), int(y)), radius

        # 2. Shape Fallback: Grayscale Circularity Detection (for black/white balls)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=8,
            maxRadius=120
        )

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # Pick largest circular contour
            best_circle = max(circles, key=lambda item: item[2])
            return (int(best_circle[0]), int(best_circle[1])), float(best_circle[2])

        return None, None


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
