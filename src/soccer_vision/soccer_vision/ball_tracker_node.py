#!/usr/bin/env python3
"""
ball_tracker_node.py
Clean & Accurate Multi-Color Soccer Ball Tracker.

Tracks colored soccer balls (Orange, Red, Yellow, Green, Blue, Pink) using
HSV color filtering with strict contour area verification to eliminate noise.

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
        self.get_logger().info('Accurate Multi-Color Ball Tracker active. Listening to /image_raw')

        # Tuned HSV ranges for vibrant ball colors under indoor lighting
        self.hsv_ranges = [
            (np.array([ 5, 80, 80]), np.array([30, 255, 255])),   # Orange / Yellow
            (np.array([160, 80, 80]), np.array([180, 255, 255])), # Red / Pink
            (np.array([ 35, 80, 80]), np.array([85, 255, 255])),  # Green
            (np.array([ 85, 80, 80]), np.array([135, 255, 255])), # Blue / Cyan
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
            self.get_logger().info(f"⚽ SOCCER BALL DETECTED -> Center X: {center[0]}, Y: {center[1]}, Radius: {radius:.1f}px")

    def process_frame(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Combine HSV color masks
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in self.hsv_ranges:
            m = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, m)

        # Morphological opening/closing to remove background noise
        combined_mask = cv2.erode(combined_mask, None, iterations=2)
        combined_mask = cv2.dilate(combined_mask, None, iterations=2)

        contours, _ = cv2.findContours(combined_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            # Require minimum area of 300 sq pixels to ignore small background spots
            if area > 300:
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                if radius > 10:
                    return (int(x), int(y)), radius

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
