#!/usr/bin/env python3
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
        
        # 1. Initialize CV Bridge
        self.bridge = CvBridge()
        
        # 2. Subscribe to the camera feed (Topic: /image_raw)
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10
        )
        self.get_logger().info('Ball Tracker Node started. Listening to /image_raw')
        
        # 3. Publisher for the ball's coordinates (Topic: /ball_position)
        # We use Point: x = screen X, y = screen Y, z = radius (distance proxy)
        self.publisher_ = self.create_publisher(Point, '/ball_position', 10)
        
        # 4. HSV color range for a standard orange/yellow soccer ball
        self.color_lower = np.array([10, 100, 100])
        self.color_upper = np.array([25, 255, 255])

    def image_callback(self, msg):
        try:
            # Convert ROS Image message to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CV Bridge Error: {e}")
            return

        # Process the frame to find the ball
        center, radius = self.process_frame(cv_image)
        
        if center is not None:
            # Ball found! Create a message and publish it
            ball_msg = Point()
            ball_msg.x = float(center[0])
            ball_msg.y = float(center[1])
            ball_msg.z = float(radius) # We use 'z' to store the radius
            self.publisher_.publish(ball_msg)
            self.get_logger().debug(f"Ball found at X:{center[0]}, Y:{center[1]}, Radius:{radius:.1f}")

    def process_frame(self, frame):
        """
        OpenCV logic to isolate the ball using HSV color filtering.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.color_lower, self.color_upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
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
        rclpy.shutdown()

if __name__ == '__main__':
    main()
