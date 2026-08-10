#!/usr/bin/env python3
"""
====================================================================
           SOCCER BOT - DYNAMIC ODOMETRY & TF PUBLISHER
====================================================================
Description:
    Node that tracks the robot's dynamic position (x, y, theta) relative
    to the fixed room map ('map' frame) and broadcasts dynamic TFs:
        map -> odom -> base_link

    This ensures that in RViz (Fixed Frame: map):
    - The room / Lidar walls stay 100% FIXED in space.
    - The 3D Robot Model moves, turns, and translates across the room!
====================================================================
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
import math
import tf2_ros

class RobotOdometryPublisher(Node):
    def __init__(self):
        super().__init__('robot_odometry')
        
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        
        # Robot position state relative to fixed map
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        
        # Velocity state
        self.vx = 0.0
        self.vth = 0.0
        
        self.last_time = self.get_clock().now()
        
        # Subscribe to velocity commands or movement inputs
        self.sub_cmd = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        # Update odometry at 20 Hz
        self.timer = self.create_timer(0.05, self.update_odometry)
        self.get_logger().info("Robot Odometry & Dynamic Map TF Publisher active.")

    def cmd_vel_callback(self, msg):
        self.vx = msg.linear.x
        self.vth = msg.angular.z

    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time

        # Calculate position change
        delta_x = (self.vx * math.cos(self.th)) * dt
        delta_y = (self.vx * math.sin(self.th)) * dt
        delta_th = self.vth * dt

        self.x += delta_x
        self.y += delta_y
        self.th += delta_th

        # Quaternion calculation for 3D rotation
        qz = math.sin(self.th / 2.0)
        qw = math.cos(self.th / 2.0)

        now = current_time.to_msg()

        # 1. Broadcast dynamic transform map -> base_link
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = 'map'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(t)

        # 2. Publish standard ROS 2 /odom message
        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = 'map'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.angular.z = self.vth
        self.odom_pub.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = RobotOdometryPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
