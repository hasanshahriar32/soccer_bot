#!/usr/bin/env python3
"""
ball_tracker_node.py
Universal Multi-Color Soccer Ball Tracker Node.

Subscribes to:
  - /image_raw (sensor_msgs/Image): Live camera stream

Publishes to:
  - /ball_position (geometry_msgs/Point): x = center_x, y = center_y, z = radius
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
        self.get_logger().info('Universal Multi-Color Ball Tracker Node started. Subscribed to /image_raw')

        # Multi-color HSV masks (Orange/Yellow, Red, Green, Blue)
        self.range_orange_yellow = (np.array([5, 70, 70]), np.array([35, 255, 255]))
        self.range_red1          = (np.array([0, 70, 70]), np.array([10, 255, 255]))
        self.range_red2          = (np.array([160, 70, 70]), np.array([180, 255, 255]))
        self.range_green         = (np.array([35, 60, 60]), np.array([85, 255, 255]))
        self.range_blue          = (np.array([90, 60, 60]), np.array([130, 255, 255]))

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
            self.get_logger().info(f"⚽ BALL DETECTED! X:{center[0]}, Y:{center[1]}, Radius:{radius:.1f}")

    def process_frame(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Create combined mask for all ball colors
        mask_oy = cv2.inRange(hsv, self.range_orange_yellow[0], self.range_orange_yellow[1])
        mask_r1 = cv2.inRange(hsv, self.range_red1[0], self.range_red1[1])
        mask_r2 = cv2.inRange(hsv, self.range_red2[0], self.range_red2[1])
        mask_g  = cv2.inRange(hsv, self.range_green[0], self.range_green[1])
        mask_b  = cv2.inRange(hsv, self.range_blue[0], self.range_blue[1])

        mask = mask_oy | mask_r1 | mask_r2 | mask_g | mask_b

        # Clean noise
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)

            if radius > 8:  # Detect ball if radius > 8px
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
