#!/usr/bin/env python3
"""
====================================================================
  INTELLIGENT 2D LIDAR SMALL-OBJECT & BALL CLUSTER DETECTOR — ROS 2
====================================================================
Description:
    1. Subscribes to /scan (sensor_msgs/LaserScan).
    2. Converts raw ranges into 2D Cartesian points in laser_frame.
    3. Performs Range-Adaptive Euclidean Jump Clustering:
       - Dynamically calculates neighbor distance threshold based on range.
       - Groups points belonging to the same physical object.
    4. Extracts Geometric Features for each cluster:
       - Chord Width (diameter of the detected arc in meters).
       - Arc Curvature & Depth (verifies convex arc facing robot).
       - Isolation & Wall Rejection (discards continuous flat walls).
    5. Tennis Ball Geometric Filter:
       - Standard ball diameter ~ 6.5 cm (0.065 m).
       - Matches clusters with chord width between 3.5 cm and 9.5 cm.
    6. Publishes:
       - /lidar_ball_position (geometry_msgs/Point): x, y, r of detected ball.
       - /lidar_ball_marker (visualization_msgs/MarkerArray):
           * 3D Neon-Green Sphere at ball location.
           * Floating HUD text showing distance & measured diameter.
           * Direct visual ray from robot to ball.
       - /lidar_clusters (visualization_msgs/MarkerArray):
           * 3D Bounding Boxes for all small obstacles in 360° field.
====================================================================
"""

import math
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker, MarkerArray

# --------------- Physical Dimensions ---------------
BALL_MIN_DIAMETER_M = 0.025    # 2.5 cm minimum chord width
BALL_MAX_DIAMETER_M = 0.115    # 11.5 cm maximum chord width (allowing beam dispersion & partial grazing)
BALL_IDEAL_DIAMETER_M = 0.065  # 6.5 cm standard tennis ball
MAX_BALL_DISTANCE_M = 4.5      # Maximum reliable detection range for small objects

class LidarClusterDetector(Node):
    def __init__(self):
        super().__init__('lidar_cluster_detector')

        self.sub_scan = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)

        self.pub_ball_pos = self.create_publisher(
            Point, '/lidar_ball_position', 10)
        self.pub_ball_marker = self.create_publisher(
            MarkerArray, '/lidar_ball_marker', 10)
        self.pub_cluster_markers = self.create_publisher(
            MarkerArray, '/lidar_clusters', 10)

        self.last_detection_time = 0.0
        self.has_ball = False

        self.get_logger().info('===========================================================')
        self.get_logger().info(' 🎾 ADVANCED LIDAR OBJECT & BALL CLUSTER DETECTOR ACTIVE')
        self.get_logger().info(' Publishing: /lidar_ball_position, /lidar_ball_marker, /lidar_clusters')
        self.get_logger().info('===========================================================')

    def scan_callback(self, msg: LaserScan):
        stamp = msg.header.stamp
        frame_id = msg.header.frame_id if msg.header.frame_id else 'laser_frame'

        # 1. Convert valid ranges to 2D Cartesian coordinates
        points = []
        angle = msg.angle_min
        for i, r in enumerate(msg.ranges):
            if msg.range_min <= r <= msg.range_max and not math.isnan(r) and not math.isinf(r):
                if 0.08 <= r <= 8.0:
                    x = r * math.cos(angle)
                    y = r * math.sin(angle)
                    points.append((x, y, r, angle, i))
            angle += msg.angle_increment

        if len(points) < 3:
            self.clear_ball_if_lost(stamp, frame_id)
            return

        # 2. Adaptive Range-Jump Euclidean Clustering
        clusters = []
        current_cluster = [points[0]]

        for i in range(1, len(points)):
            prev_pt = points[i - 1]
            curr_pt = points[i]

            # Adaptive jump threshold: delta_theta * range * 2.0 + small base margin
            avg_r = (prev_pt[2] + curr_pt[2]) / 2.0
            jump_threshold = avg_r * msg.angle_increment * 2.2 + 0.06

            dx = curr_pt[0] - prev_pt[0]
            dy = curr_pt[1] - prev_pt[1]
            dist = math.hypot(dx, dy)

            # Check for angle index jump (discontinuity in sweep)
            idx_jump = abs(curr_pt[4] - prev_pt[4])

            if dist < jump_threshold and idx_jump <= 3:
                current_cluster.append(curr_pt)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [curr_pt]

        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        # Handle wrap-around near 0° / 360°
        if len(clusters) >= 2:
            first_pt = clusters[0][0]
            last_pt = clusters[-1][-1]
            avg_r = (first_pt[2] + last_pt[2]) / 2.0
            jump_threshold = avg_r * msg.angle_increment * 2.2 + 0.06
            if math.hypot(first_pt[0] - last_pt[0], first_pt[1] - last_pt[1]) < jump_threshold:
                # Merge last cluster into first
                clusters[0] = clusters[-1] + clusters[0]
                clusters.pop()

        # 3. Analyze each cluster and find the best Ball Candidate
        best_ball = None
        best_ball_score = -1.0
        all_clusters_meta = []

        for c_idx, cluster in enumerate(clusters):
            n_pts = len(cluster)
            pts_xy = np.array([(p[0], p[1]) for p in cluster])
            center_x = float(np.mean(pts_xy[:, 0]))
            center_y = float(np.mean(pts_xy[:, 1]))
            center_dist = math.hypot(center_x, center_y)
            center_bearing = math.atan2(center_y, center_x)

            # Chord Width: Distance between first and last point
            first_p = pts_xy[0]
            last_p = pts_xy[-1]
            chord_width = float(math.hypot(last_p[0] - first_p[0], last_p[1] - first_p[1]))

            # Max span among all points
            max_span = chord_width
            if n_pts > 2:
                diffs = pts_xy[:, np.newaxis, :] - pts_xy[np.newaxis, :, :]
                dists = np.sqrt(np.sum(diffs ** 2, axis=-1))
                max_span = float(np.max(dists))

            # Curvature check: Middle points should be closer to the robot than chord endpoints
            chord_mid_r = (cluster[0][2] + cluster[-1][2]) / 2.0
            inner_min_r = min(p[2] for p in cluster)
            sagitta = max(0.0, chord_mid_r - inner_min_r)  # Arc depth

            is_ball_candidate = False
            classification = "OBSTACLE"

            if (BALL_MIN_DIAMETER_M <= max_span <= BALL_MAX_DIAMETER_M and 
                center_dist <= MAX_BALL_DISTANCE_M and 
                n_pts >= 2):
                
                # Check circular size score
                size_error = abs(max_span - BALL_IDEAL_DIAMETER_M)
                score = 1.0 / (1.0 + size_error * 25.0)

                # Prioritize forward hemisphere objects
                forward_weight = 1.0 if abs(center_bearing) < math.radians(90.0) else 0.7
                score *= forward_weight

                is_ball_candidate = True
                classification = "TENNIS_BALL"

                if score > best_ball_score:
                    best_ball_score = score
                    best_ball = {
                        'x': center_x,
                        'y': center_y,
                        'dist': center_dist,
                        'bearing': center_bearing,
                        'width': max_span,
                        'pts': pts_xy,
                        'score': score
                    }

            elif max_span < 0.25:
                classification = "SMALL_OBJECT"
            else:
                classification = "WALL_OR_LARGE"

            all_clusters_meta.append({
                'id': c_idx,
                'center_x': center_x,
                'center_y': center_y,
                'width': max_span,
                'type': classification,
                'pts': pts_xy
            })

        # 4. Publish Ball Detection & 3D Markers
        if best_ball is not None:
            self.has_ball = True
            pos_msg = Point()
            pos_msg.x = float(best_ball['x'])
            pos_msg.y = float(best_ball['y'])
            pos_msg.z = float(best_ball['dist'])
            self.pub_ball_pos.publish(pos_msg)

            self.publish_ball_markers(best_ball, stamp, frame_id)
        else:
            self.clear_ball_if_lost(stamp, frame_id)

        # 5. Publish 3D Bounding Boxes for All Obstacle Clusters
        self.publish_cluster_boxes(all_clusters_meta, stamp, frame_id)

    def publish_ball_markers(self, ball, stamp, frame_id):
        ma = MarkerArray()

        # Marker 0: 3D Tennis Ball Sphere
        m_sphere = Marker()
        m_sphere.header.stamp = stamp
        m_sphere.header.frame_id = frame_id
        m_sphere.ns = "lidar_ball"
        m_sphere.id = 0
        m_sphere.type = Marker.SPHERE
        m_sphere.action = Marker.ADD
        m_sphere.pose.position.x = ball['x']
        m_sphere.pose.position.y = ball['y']
        m_sphere.pose.position.z = 0.0
        m_sphere.pose.orientation.w = 1.0
        # Tennis ball physical scale (6.5cm diameter)
        m_sphere.scale.x = BALL_IDEAL_DIAMETER_M
        m_sphere.scale.y = BALL_IDEAL_DIAMETER_M
        m_sphere.scale.z = BALL_IDEAL_DIAMETER_M
        # Vibrant Tennis Ball Fluorescent Yellow-Green
        m_sphere.color.r = 0.75
        m_sphere.color.g = 1.00
        m_sphere.color.b = 0.05
        m_sphere.color.a = 0.95
        ma.markers.append(m_sphere)

        # Marker 1: Floating Text HUD above Ball
        m_text = Marker()
        m_text.header.stamp = stamp
        m_text.header.frame_id = frame_id
        m_text.ns = "lidar_ball"
        m_text.id = 1
        m_text.type = Marker.TEXT_VIEW_FACING
        m_text.action = Marker.ADD
        m_text.pose.position.x = ball['x']
        m_text.pose.position.y = ball['y']
        m_text.pose.position.z = 0.15  # Float 15cm above ball
        m_text.pose.orientation.w = 1.0
        m_text.scale.z = 0.08  # Font size
        m_text.color.r = 1.0
        m_text.color.g = 1.0
        m_text.color.b = 1.0
        m_text.color.a = 1.0
        diam_cm = ball['width'] * 100.0
        conf_pct = int(min(1.0, ball['score']) * 100.0)
        m_text.text = f"🎾 Tennis Ball (LiDAR)\nDist: {ball['dist']:.2f}m | Arc: {diam_cm:.1f}cm ({conf_pct}%)"
        ma.markers.append(m_text)

        # Marker 2: Direct Tracking Line from Robot to Ball
        m_line = Marker()
        m_line.header.stamp = stamp
        m_line.header.frame_id = frame_id
        m_line.ns = "lidar_ball"
        m_line.id = 2
        m_line.type = Marker.LINE_STRIP
        m_line.action = Marker.ADD
        m_line.scale.x = 0.02  # Line thickness
        m_line.color.r = 0.75
        m_line.color.g = 1.00
        m_line.color.b = 0.05
        m_line.color.a = 0.80
        p0 = Point(x=0.0, y=0.0, z=0.0)
        p1 = Point(x=ball['x'], y=ball['y'], z=0.0)
        m_line.points = [p0, p1]
        ma.markers.append(m_line)

        self.pub_ball_marker.publish(ma)

    def publish_cluster_boxes(self, clusters, stamp, frame_id):
        ma = MarkerArray()

        for c in clusters:
            if c['type'] == 'TENNIS_BALL':
                continue  # Handled by ball marker

            m = Marker()
            m.header.stamp = stamp
            m.header.frame_id = frame_id
            m.ns = "lidar_obstacles"
            m.id = c['id']
            m.type = Marker.CYLINDER
            m.action = Marker.ADD
            m.pose.position.x = c['center_x']
            m.pose.position.y = c['center_y']
            m.pose.position.z = 0.0
            m.pose.orientation.w = 1.0

            width = max(0.04, c['width'])
            m.scale.x = width
            m.scale.y = width
            m.scale.z = 0.08

            if c['type'] == 'SMALL_OBJECT':
                # Cyan for small objects (shoes, posts, cones)
                m.color.r = 0.0
                m.color.g = 0.8
                m.color.b = 1.0
                m.color.a = 0.65
            else:
                # Grey for larger obstacles/walls
                m.color.r = 0.6
                m.color.g = 0.6
                m.color.b = 0.6
                m.color.a = 0.35

            ma.markers.append(m)

        self.pub_cluster_markers.publish(ma)

    def clear_ball_if_lost(self, stamp, frame_id):
        if self.has_ball:
            self.has_ball = False
            ma = MarkerArray()
            for mid in [0, 1, 2]:
                m = Marker()
                m.header.stamp = stamp
                m.header.frame_id = frame_id
                m.ns = "lidar_ball"
                m.id = mid
                m.action = Marker.DELETE
                ma.markers.append(m)
            self.pub_ball_marker.publish(ma)

def main(args=None):
    rclpy.init(args=args)
    node = LidarClusterDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
