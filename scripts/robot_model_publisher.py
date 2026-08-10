#!/usr/bin/env python3
"""
====================================================================
               SOCCER BOT ROBOT MODEL & TF PUBLISHER
====================================================================
Description:
    ROS 2 Jazzy node that publishes the official repository URDF model
    (/robot_description) with TRANSIENT_LOCAL QoS for RViz compatibility
    and broadcasts the full 3D Transform (TF) tree.

Physical Dimensions & Joint Offsets:
    - Chassis Box:       0.33 m (L) x 0.17 m (W) x 0.11 m (H)
    - Left/Right Wheels: Radius = 0.033 m, Length = 0.040 m
                        Rear position offset: X = -0.115 m, Y = +/-0.105 m
    - YDLidar X4:        Radius = 0.035 m, Length = 0.040 m
                        Position offset: X = 0.000 m, Y = -0.019 m, Z = 0.090 m
    - Pi Camera V2:      0.010 m x 0.030 m x 0.030 m
                        Front position offset: X = 0.165 m, Y = +0.020 m, Z = 0.045 m
====================================================================
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import TransformStamped
from rclpy.qos import QoSProfile, DurabilityPolicy
import tf2_ros
import os

URDF_PATH = "/mnt/c/Users/taufi/Desktop/soccer_bot/scripts/robot.urdf"

class RobotModelPublisher(Node):
    def __init__(self):
        super().__init__('robot_model_publisher')
        
        # 1. Setup QoS Profile (TRANSIENT_LOCAL required by RViz2)
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.description_pub = self.create_publisher(String, '/robot_description', qos)
        self.tf_broadcaster = tf2_ros.StaticTransformBroadcaster(self)
        
        # 2. Read URDF file from disk
        if not os.path.exists(URDF_PATH):
            self.get_logger().error(f"URDF file not found at: {URDF_PATH}")
            raise FileNotFoundError(f"Missing URDF at {URDF_PATH}")
            
        with open(URDF_PATH, 'r') as f:
            self.urdf_content = f.read()
            
        # 3. Perform Initial Broadcast
        self.publish_all()
        
        # 4. Timer loop to maintain state (1.0 Hz)
        self.timer = self.create_timer(1.0, self.publish_all)
        self.get_logger().info("Soccer Bot Robot Model & TF Publisher initialized successfully.")

    def publish_all(self):
        self.publish_urdf()
        self.publish_tf_tree()

    def publish_urdf(self):
        msg = String()
        msg.data = self.urdf_content
        self.description_pub.publish(msg)

    def publish_tf_tree(self):
        now = self.get_clock().now().to_msg()
        tfs = []

        # map -> base_link
        t_map = TransformStamped()
        t_map.header.stamp = now
        t_map.header.frame_id = 'map'
        t_map.child_frame_id = 'base_link'
        t_map.transform.rotation.w = 1.0
        tfs.append(t_map)

        # base_link -> chassis
        t_chassis = TransformStamped()
        t_chassis.header.stamp = now
        t_chassis.header.frame_id = 'base_link'
        t_chassis.child_frame_id = 'chassis'
        t_chassis.transform.rotation.w = 1.0
        tfs.append(t_chassis)

        # chassis -> left_wheel (Rear Left: X = -0.115, Y = +0.105, Z = 0.033)
        t_lw = TransformStamped()
        t_lw.header.stamp = now
        t_lw.header.frame_id = 'chassis'
        t_lw.child_frame_id = 'left_wheel'
        t_lw.transform.translation.x = -0.115
        t_lw.transform.translation.y = 0.105
        t_lw.transform.translation.z = 0.033
        t_lw.transform.rotation.x = -0.7071068
        t_lw.transform.rotation.w = 0.7071068
        tfs.append(t_lw)

        # chassis -> right_wheel (Rear Right: X = -0.115, Y = -0.105, Z = 0.033)
        t_rw = TransformStamped()
        t_rw.header.stamp = now
        t_rw.header.frame_id = 'chassis'
        t_rw.child_frame_id = 'right_wheel'
        t_rw.transform.translation.x = -0.115
        t_rw.transform.translation.y = -0.105
        t_rw.transform.translation.z = 0.033
        t_rw.transform.rotation.x = -0.7071068
        t_rw.transform.rotation.w = 0.7071068
        tfs.append(t_rw)

        # base_link -> laser_frame (YDLidar X4: X = 0.0, Y = -0.019, Z = 0.090)
        t_laser = TransformStamped()
        t_laser.header.stamp = now
        t_laser.header.frame_id = 'base_link'
        t_laser.child_frame_id = 'laser_frame'
        t_laser.transform.translation.x = 0.0
        t_laser.transform.translation.y = -0.019
        t_laser.transform.translation.z = 0.090
        t_laser.transform.rotation.w = 1.0
        tfs.append(t_laser)

        # base_link -> camera_link (Pi Camera V2: X = 0.165, Y = +0.020, Z = 0.045)
        t_cam = TransformStamped()
        t_cam.header.stamp = now
        t_cam.header.frame_id = 'base_link'
        t_cam.child_frame_id = 'camera_link'
        t_cam.transform.translation.x = 0.165
        t_cam.transform.translation.y = 0.020
        t_cam.transform.translation.z = 0.045
        t_cam.transform.rotation.x = -0.5
        t_cam.transform.rotation.y = 0.5
        t_cam.transform.rotation.z = -0.5
        t_cam.transform.rotation.w = 0.5
        tfs.append(t_cam)

        # Send complete TF array
        self.tf_broadcaster.sendTransform(tfs)

def main(args=None):
    rclpy.init(args=args)
    node = RobotModelPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
