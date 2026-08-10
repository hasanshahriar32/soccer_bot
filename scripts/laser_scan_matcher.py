#!/usr/bin/env python3
"""
====================================================================
     STABLE 2D LIDAR SCAN-TO-REFERENCE ICP ODOMETRY NODE
====================================================================
Description:
    Estimates robot pose by matching each new Lidar scan against a
    FIXED reference scan (captured at startup). This eliminates
    cumulative drift and frame vibration.

    Key Design:
    - Reference scan captured once at startup (the "room anchor").
    - Each new scan is matched against this fixed reference using
      Iterative Closest Point (ICP) with nearest-neighbor search.
    - Heavy deadzone filtering: ignores displacements < 1cm / 1°.
    - Result: Room walls stay rock-solid in RViz. Robot model moves
              only when real physical movement is detected.
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
from scipy.spatial import KDTree


class StableScanMatcher(Node):
    def __init__(self):
        super().__init__('stable_scan_matcher')

        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)

        # Robot pose in fixed map frame
        self.pose_x = 0.0
        self.pose_y = 0.0
        self.pose_yaw = 0.0

        # Smoothed pose (what we actually publish)
        self.pub_x = 0.0
        self.pub_y = 0.0
        self.pub_yaw = 0.0

        # Reference scan (room anchor) - set from first good scan
        self.ref_points = None
        self.ref_tree = None  # KDTree for fast nearest-neighbor
        self.warmup_count = 0
        self.WARMUP_SCANS = 5  # Skip first N scans to let lidar stabilize

        self.get_logger().info(
            "Stable Scan-to-Reference ICP Matcher initialized. "
            "Waiting for reference scan...")

    def scan_to_points(self, scan_msg):
        """Convert LaserScan to 2D cartesian points, filtering noise."""
        ranges = np.array(scan_msg.ranges)
        n = len(ranges)
        angles = np.linspace(
            scan_msg.angle_min, scan_msg.angle_max, n)

        valid = np.isfinite(ranges) & (ranges >= 0.15) & (ranges <= 6.0)
        if np.sum(valid) < 40:
            return None

        r = ranges[valid]
        a = angles[valid]
        xs = r * np.cos(a)
        ys = r * np.sin(a)
        return np.column_stack((xs, ys))

    def icp_match(self, ref_tree, ref_pts, src_pts, max_iter=15):
        """
        Iterative Closest Point matching of src_pts against ref_pts.
        Returns (dx, dy, dtheta) transform from src frame to ref frame.
        """
        pts = src_pts.copy()
        total_R = np.eye(2)
        total_t = np.zeros(2)

        for _ in range(max_iter):
            # Find nearest neighbors in reference
            dists, idxs = ref_tree.query(pts)

            # Reject outliers (distance > 0.5m)
            inlier_mask = dists < 0.5
            if np.sum(inlier_mask) < 20:
                break

            matched_ref = ref_pts[idxs[inlier_mask]]
            matched_src = pts[inlier_mask]

            # Compute centroids
            c_ref = np.mean(matched_ref, axis=0)
            c_src = np.mean(matched_src, axis=0)

            # Center the point sets
            ref_c = matched_ref - c_ref
            src_c = matched_src - c_src

            # SVD for optimal rotation
            H = src_c.T @ ref_c
            U, _, Vt = np.linalg.svd(H)
            R = Vt.T @ U.T

            if np.linalg.det(R) < 0:
                Vt[1, :] *= -1
                R = Vt.T @ U.T

            t = c_ref - R @ c_src

            # Apply transform
            pts = (R @ pts.T).T + t

            total_R = R @ total_R
            total_t = R @ total_t + t

            # Check convergence
            if np.linalg.norm(t) < 0.001:
                break

        dtheta = math.atan2(total_R[1, 0], total_R[0, 0])
        dx = total_t[0]
        dy = total_t[1]
        return dx, dy, dtheta

    def scan_callback(self, scan_msg):
        curr_points = self.scan_to_points(scan_msg)
        if curr_points is None:
            return

        # Warmup: skip first few noisy scans
        self.warmup_count += 1
        if self.warmup_count <= self.WARMUP_SCANS:
            return

        # Capture reference scan (room anchor) from first stable scan
        if self.ref_points is None:
            self.ref_points = curr_points.copy()
            self.ref_tree = KDTree(self.ref_points)
            self.get_logger().info(
                f"Reference scan captured ({len(self.ref_points)} points). "
                f"Room anchor locked.")
            self.publish_tf_and_odom(scan_msg.header.stamp)
            return

        # Run ICP: match current scan against fixed reference
        dx, dy, dyaw = self.icp_match(
            self.ref_tree, self.ref_points, curr_points)

        # Deadzone: ignore tiny displacements (sensor noise)
        if abs(dx) < 0.01:
            dx = 0.0
        if abs(dy) < 0.01:
            dy = 0.0
        if abs(dyaw) < math.radians(1.0):
            dyaw = 0.0

        # Set raw pose from ICP result (absolute, not cumulative)
        raw_x = dx
        raw_y = dy
        raw_yaw = dyaw

        # Heavy exponential smoothing (alpha=0.1 for stability)
        alpha = 0.1
        self.pub_x = (1.0 - alpha) * self.pub_x + alpha * raw_x
        self.pub_y = (1.0 - alpha) * self.pub_y + alpha * raw_y
        self.pub_yaw = (1.0 - alpha) * self.pub_yaw + alpha * raw_yaw

        self.publish_tf_and_odom(scan_msg.header.stamp)

    def publish_tf_and_odom(self, stamp):
        qz = math.sin(self.pub_yaw / 2.0)
        qw = math.cos(self.pub_yaw / 2.0)

        # Broadcast dynamic TF: map -> base_link
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'map'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = float(self.pub_x)
        t.transform.translation.y = float(self.pub_y)
        t.transform.translation.z = 0.0
        t.transform.rotation.z = float(qz)
        t.transform.rotation.w = float(qw)
        self.tf_broadcaster.sendTransform(t)

        # Publish Odometry message
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'map'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = float(self.pub_x)
        odom.pose.pose.position.y = float(self.pub_y)
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = float(qz)
        odom.pose.pose.orientation.w = float(qw)
        self.odom_pub.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = StableScanMatcher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
