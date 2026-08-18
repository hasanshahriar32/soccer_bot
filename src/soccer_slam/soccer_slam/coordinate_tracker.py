#!/usr/bin/env python3
"""
====================================================================
Soccer Bot SLAM Spatial Coordinate Tracker Node
====================================================================
Subscribes to TF transformations between 'map' and 'base_link' to
extract real-time (x, y, theta) coordinates.

Publishes:
  - /robot_map_pose    (geometry_msgs/PoseStamped) : Live world pose
  - /robot_trajectory  (nav_msgs/Path)            : Full travel path
====================================================================
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
import tf2_ros
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path


def euler_from_quaternion(x, y, z, w):
    """Convert quaternion (x, y, z, w) to euler roll, pitch, yaw (radians)."""
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.atan2(t3, t4)
    return yaw_z


class CoordinateTrackerNode(Node):
    def __init__(self):
        super().__init__('soccer_coordinate_tracker')

        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('publish_rate', 10.0)

        self.map_frame = self.get_parameter('map_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value
        rate = self.get_parameter('publish_rate').get_parameter_value().double_value

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.pose_pub = self.create_publisher(PoseStamped, '/robot_map_pose', 10)
        self.path_pub = self.create_publisher(Path, '/robot_trajectory', 10)

        self.trajectory_path = Path()
        self.trajectory_path.header.frame_id = self.map_frame

        self.timer = self.create_timer(1.0 / rate, self.track_pose_callback)
        self.last_log_time = self.get_clock().now()

        self.get_logger().info(f"[SLAM TRACKER] Coordinate Tracker initialized. Tracking '{self.base_frame}' in '{self.map_frame}'.")

    def track_pose_callback(self):
        try:
            # Lookup latest transform between map and base_link
            t = self.tf_buffer.lookup_transform(
                self.map_frame,
                self.base_frame,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.1)
            )

            # Construct PoseStamped
            current_pose = PoseStamped()
            current_pose.header.stamp = self.get_clock().now().to_msg()
            current_pose.header.frame_id = self.map_frame
            current_pose.pose.position.x = t.transform.translation.x
            current_pose.pose.position.y = t.transform.translation.y
            current_pose.pose.position.z = t.transform.translation.z
            current_pose.pose.orientation = t.transform.rotation

            # Publish live pose
            self.pose_pub.publish(current_pose)

            # Append to trajectory path
            self.trajectory_path.header.stamp = current_pose.header.stamp
            self.trajectory_path.poses.append(current_pose)

            # Limit path length to 2000 points to prevent memory growth
            if len(self.trajectory_path.poses) > 2000:
                self.trajectory_path.poses.pop(0)

            self.path_pub.publish(self.trajectory_path)

            # Calculate heading in degrees
            q = t.transform.rotation
            yaw_rad = euler_from_quaternion(q.x, q.y, q.z, q.w)
            yaw_deg = math.degrees(yaw_rad)

            # Periodic terminal telemetry log (every 1.5s)
            now = self.get_clock().now()
            if (now - self.last_log_time).nanoseconds > 1.5e9:
                self.last_log_time = now
                self.get_logger().info(
                    f"📍 POSE: X={current_pose.pose.position.x:+.3f}m | "
                    f"Y={current_pose.pose.position.y:+.3f}m | "
                    f"Heading={yaw_deg:+.1f}° | Path Points={len(self.trajectory_path.poses)}"
                )

        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
            pass


def main(args=None):
    rclpy.init(args=args)
    node = CoordinateTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
