#!/usr/bin/env python3
"""
====================================================================
           SOCCER BOT - ROBUST PATH TRAJECTORY PUBLISHER
====================================================================
Subscribes to the SLAM/Odom TF frame (/map -> /base_link) and
publishes a nav_msgs/Path topic to draw a line behind the robot.
====================================================================
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
import tf2_ros

class RobotPathPublisher(Node):
    def __init__(self):
        super().__init__('robot_path_publisher')
        
        self.path_pub = self.create_publisher(Path, '/robot_path', 10)
        
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        self.path = Path()
        self.path.header.frame_id = 'map'
        
        # Check transform every 100ms (10Hz)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info("Robot Path Publisher Initialized (Publishing /robot_path)")

    def timer_callback(self):
        try:
            # Look up transform from map to base_link
            t = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            
            pose = PoseStamped()
            pose.header = t.header
            pose.pose.position.x = t.transform.translation.x
            pose.pose.position.y = t.transform.translation.y
            pose.pose.position.z = t.transform.translation.z
            pose.pose.orientation = t.transform.rotation
            
            # Check distance from last point to avoid duplicate entries
            should_add = True
            if len(self.path.poses) > 0:
                last_pose = self.path.poses[-1].pose.position
                dist = ((pose.pose.position.x - last_pose.x) ** 2 + 
                        (pose.pose.position.y - last_pose.y) ** 2) ** 0.5
                # Only add if robot moved at least 3cm
                if dist < 0.03:
                    should_add = False
            
            if should_add:
                self.path.poses.append(pose)
                self.path.header.stamp = self.get_clock().now().to_msg()
                self.path_pub.publish(self.path)
                
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
            pass

def main(args=None):
    rclpy.init(args=args)
    node = RobotPathPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
