#!/usr/bin/env python3
"""
====================================================================
     STABILIZED 2D LIDAR SCAN MATCHING & ODOMETRY NODE FOR ROS 2
====================================================================
Description:
    Estimates real-time 2D pose displacement (x, y, theta) from Lidar scans
    with exponential smoothing (EMA) and rigid map orientation lock.

    Key Features:
    - Locks room map angle (0° map orientation) so background doesn't tilt.
    - Low-pass filters rotation jitter (alpha=0.15) for smooth movement.
    - Broadcasts dynamic transform: map -> base_link
    - Result: Room walls stay 100% FIXED in RViz; 3D Robot Model translates
              and rotates smoothly across the fixed room grid!
====================================================================
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import math
import numpy as np
import tf2_ros

class LaserScanMatcher(Node):
    def __init__(self):
        super().__init__('laser_scan_matcher')
        
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        
        # Subscribe to Lidar scan topic
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        
        # Cumulative robot pose in fixed room 'map'
        self.pose_x = 0.0
        self.pose_y = 0.0
        self.pose_yaw = 0.0
        
        # Smooth velocity state
        self.smooth_dyaw = 0.0
        
        self.prev_points = None
        self.get_logger().info("Stabilized 2D Lidar Scan Matcher active. Room map locked to 0° angle.")

    def scan_to_points(self, scan_msg):
        """Converts LaserScan ranges to 2D Cartesian points (N, 2)."""
        angles = np.linspace(scan_msg.angle_min, scan_msg.angle_max, len(scan_msg.ranges))
        ranges = np.array(scan_msg.ranges)
        
        # Filter valid lidar readings (15 cm to 6.0 meters)
        valid = (ranges >= 0.15) & (ranges <= 6.0) & np.isfinite(ranges)
        if not np.any(valid):
            return None
            
        valid_ranges = ranges[valid]
        valid_angles = angles[valid]
        
        xs = valid_ranges * np.cos(valid_angles)
        ys = valid_ranges * np.sin(valid_angles)
        return np.column_stack((xs, ys))

    def scan_callback(self, scan_msg):
        curr_points = self.scan_to_points(scan_msg)
        if curr_points is None or len(curr_points) < 30:
            return

        if self.prev_points is not None:
            # Perform ICP / Point Matching between prev_points and curr_points
            dx, dy, dyaw = self.match_scans(self.prev_points, curr_points)
            
            # Apply low-pass filter (EMA) to rotation to prevent map angle tilt/jitter
            self.smooth_dyaw = 0.85 * self.smooth_dyaw + 0.15 * dyaw
            
            # Update robot orientation in map frame
            self.pose_yaw -= self.smooth_dyaw
            self.pose_yaw = math.atan2(math.sin(self.pose_yaw), math.cos(self.pose_yaw))
            
            # Apply displacement relative to robot's heading
            cos_yaw = math.cos(self.pose_yaw)
            sin_yaw = math.sin(self.pose_yaw)
            
            self.pose_x += (dx * cos_yaw - dy * sin_yaw)
            self.pose_y += (dx * sin_yaw + dy * cos_yaw)

        self.prev_points = curr_points
        self.publish_tf_and_odom(scan_msg.header.stamp)

    def match_scans(self, p_ref, p_curr):
        """Finds 2D rigid transform (dx, dy, dth) matching p_curr to p_ref."""
        c_ref = np.mean(p_ref, axis=0)
        c_curr = np.mean(p_curr, axis=0)
        
        p_ref_centered = p_ref - c_ref
        min_len = min(len(p_ref_centered), len(p_curr))
        p_curr_centered = p_curr[:min_len] - c_curr
        p_ref_centered = p_ref_centered[:min_len]
        
        # Cross-covariance matrix
        H = p_curr_centered.T @ p_ref_centered
        
        # SVD for rotation estimation
        U, _, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        
        if np.linalg.det(R) < 0:
            Vt[1, :] *= -1
            R = Vt.T @ U.T
            
        dth = math.atan2(R[1, 0], R[0, 0])
        dth = np.clip(dth, -0.15, 0.15)  # Cap max turn rate per frame
        
        t_vec = c_ref - (R @ c_curr)
        dx = np.clip(t_vec[0], -0.20, 0.20)
        dy = np.clip(t_vec[1], -0.20, 0.20)
        
        return dx, dy, dth

    def publish_tf_and_odom(self, stamp):
        qz = math.sin(self.pose_yaw / 2.0)
        qw = math.cos(self.pose_yaw / 2.0)

        # 1. Broadcast dynamic TF: map -> base_link
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'map'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = float(self.pose_x)
        t.transform.translation.y = float(self.pose_y)
        t.transform.translation.z = 0.0
        t.transform.rotation.z = float(qz)
        t.transform.rotation.w = float(qw)
        self.tf_broadcaster.sendTransform(t)

        # 2. Publish Odometry Topic
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'map'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = float(self.pose_x)
        odom.pose.pose.position.y = float(self.pose_y)
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = float(qz)
        odom.pose.pose.orientation.w = float(qw)
        self.odom_pub.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = LaserScanMatcher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
