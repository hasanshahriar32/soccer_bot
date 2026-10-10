#!/usr/bin/env python3
"""
====================================================================
               SOCCER BOT ROBOT MODEL & TF PUBLISHER
====================================================================
Description:
    ROS 2 Jazzy node that publishes the official repository URDF model
    (/robot_description) with TRANSIENT_LOCAL QoS for RViz compatibility,
    publishes live joint states (/joint_states), and broadcasts the full
    3D Transform (TF) tree including dynamic articulation for the 4-DOF
    robotic arm synchronized with the Pi arm server (Port 9001).

Physical Dimensions & Joint Offsets:
    - Chassis Box:       0.33 m (L) x 0.17 m (W) x 0.11 m (H)
    - Left/Right Wheels: Radius = 0.033 m, Length = 0.040 m
                        Rear position offset: X = -0.115 m, Y = +/-0.105 m
    - YDLidar X4:        Radius = 0.035 m, Length = 0.040 m
                        Position offset: X = 0.000 m, Y = -0.019 m, Z = 0.090 m
    - Pi Camera V2:      0.010 m x 0.030 m x 0.030 m
                        Front position offset: X = 0.165 m, Y = +0.020 m, Z = 0.045 m
    - 4-DOF Robotic Arm:
        * Arm Mount:     X = 0.10 m, Y = 0.0 m, Z = 0.11 m (Top Deck)
        * Base Turret:   Yaw: 0° to 180° (Center 90°)
        * Shoulder Spar: Pitch: 0° to 180° (Length: 0.10 m)
        * Elbow Forearm: Pitch: 0° to 180° (Length: 0.10 m)
        * Gripper Claws: Opening: 90° (Clamp) to 270° (Wide open)
====================================================================
"""

import os
import sys
import time
import math
import json
import socket
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import JointState
from geometry_msgs.msg import TransformStamped
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
import tf2_ros

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
URDF_PATH = os.path.join(SCRIPT_DIR, "robot.urdf")

def discover_pi_ip():
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        return sys.argv[1]
    candidates = ["192.168.0.135", "10.127.69.146", "10.61.32.146", "10.72.30.146"]
    for ip in candidates:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.25)
            if s.connect_ex((ip, 22)) == 0 or s.connect_ex((ip, 9001)) == 0:
                s.close()
                return ip
            s.close()
        except Exception:
            pass
    return "192.168.0.135"

def euler_to_quaternion(roll, pitch, yaw):
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    q_w = cr * cp * cy + sr * sp * sy
    q_x = sr * cp * cy - cr * sp * sy
    q_y = cr * sp * cy + sr * cp * sy
    q_z = cr * cp * sy - sr * sp * cy
    return q_x, q_y, q_z, q_w

class RobotModelPublisher(Node):
    def __init__(self):
        super().__init__('robot_model_publisher')
        
        # 1. Setup QoS Profiles
        desc_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.description_pub = self.create_publisher(String, '/robot_description', desc_qos)
        
        joint_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self.joint_pub = self.create_publisher(JointState, '/joint_states', joint_qos)
        
        # TF Broadcasters (Static transforms & Live dynamic transforms)
        self.static_tf_broadcaster = tf2_ros.StaticTransformBroadcaster(self)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        # 2. Read URDF file from disk
        if not os.path.exists(URDF_PATH):
            self.get_logger().error(f"URDF file not found at: {URDF_PATH}")
            raise FileNotFoundError(f"Missing URDF at {URDF_PATH}")
            
        with open(URDF_PATH, 'r') as f:
            self.urdf_content = f.read()
            
        # 3. Arm Status State & Background Poller
        self.pi_ip = discover_pi_ip()
        self.arm_port = 9001
        self.base_deg = 90.0
        self.shoulder_deg = 45.0
        self.elbow_deg = 45.0
        self.gripper_deg = 180.0
        self.arm_connected = False
        self.lock = threading.Lock()
        
        self.running = True
        self.poll_thread = threading.Thread(target=self._arm_poll_loop, daemon=True)
        self.poll_thread.start()
        
        # 4. Publish static base transforms once
        self.publish_static_transforms()
        
        # 5. Fast loop (20 Hz) for URDF, JointState and live arm TF
        self.timer = self.create_timer(0.05, self.update_cycle)
        
        # Also maintain 1 Hz URDF latched re-broadcast
        self.urdf_timer = self.create_timer(1.0, self.publish_urdf)
        
        self.get_logger().info(f"Soccer Bot Robot Model & TF Publisher initialized (Pi Target: {self.pi_ip}:{self.arm_port}).")

    def _arm_poll_loop(self):
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(0.35)
                sock.connect((self.pi_ip, self.arm_port))
                sock.sendall(b'{"action": "status"}\n')
                raw = sock.recv(1024).decode('utf-8').strip()
                sock.close()
                if raw:
                    data = json.loads(raw)
                    if data.get('status') == 'OK':
                        with self.lock:
                            self.base_deg = float(data.get('base', self.base_deg))
                            self.shoulder_deg = float(data.get('shoulder', self.shoulder_deg))
                            self.elbow_deg = float(data.get('albo', self.elbow_deg))
                            self.gripper_deg = float(data.get('gripper', self.gripper_deg))
                            self.arm_connected = bool(data.get('connected', True))
            except Exception:
                with self.lock:
                    self.arm_connected = False
            time.sleep(0.08)

    def publish_urdf(self):
        msg = String()
        msg.data = self.urdf_content
        self.description_pub.publish(msg)

    def publish_static_transforms(self):
        now = self.get_clock().now().to_msg()
        tfs = []

        # base_link -> chassis
        t_chassis = TransformStamped()
        t_chassis.header.stamp = now
        t_chassis.header.frame_id = 'base_link'
        t_chassis.child_frame_id = 'chassis'
        t_chassis.transform.rotation.w = 1.0
        tfs.append(t_chassis)

        # chassis -> left_wheel
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

        # chassis -> right_wheel
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

        # base_link -> laser_frame
        t_laser = TransformStamped()
        t_laser.header.stamp = now
        t_laser.header.frame_id = 'base_link'
        t_laser.child_frame_id = 'laser_frame'
        t_laser.transform.translation.x = 0.0
        t_laser.transform.translation.y = -0.019
        t_laser.transform.translation.z = 0.090
        t_laser.transform.rotation.w = 1.0
        tfs.append(t_laser)

        # base_link -> camera_link
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

        # chassis -> arm_mount (Mount on top deck)
        t_mount = TransformStamped()
        t_mount.header.stamp = now
        t_mount.header.frame_id = 'chassis'
        t_mount.child_frame_id = 'arm_mount'
        t_mount.transform.translation.x = 0.10
        t_mount.transform.translation.y = 0.0
        t_mount.transform.translation.z = 0.11
        t_mount.transform.rotation.w = 1.0
        tfs.append(t_mount)

        # arm_elbow_link -> arm_wrist_link
        t_wrist = TransformStamped()
        t_wrist.header.stamp = now
        t_wrist.header.frame_id = 'arm_elbow_link'
        t_wrist.child_frame_id = 'arm_wrist_link'
        t_wrist.transform.translation.x = 0.10
        t_wrist.transform.translation.y = 0.0
        t_wrist.transform.translation.z = 0.0
        t_wrist.transform.rotation.w = 1.0
        tfs.append(t_wrist)

        # odom -> base_link
        t_odom = TransformStamped()
        t_odom.header.stamp = now
        t_odom.header.frame_id = 'odom'
        t_odom.child_frame_id = 'base_link'
        t_odom.transform.rotation.w = 1.0
        tfs.append(t_odom)

        # map -> odom
        t_map = TransformStamped()
        t_map.header.stamp = now
        t_map.header.frame_id = 'map'
        t_map.child_frame_id = 'odom'
        t_map.transform.rotation.w = 1.0
        tfs.append(t_map)

        self.static_tf_broadcaster.sendTransform(tfs)

    def update_cycle(self):
        now = self.get_clock().now().to_msg()
        
        with self.lock:
            b_deg = self.base_deg
            s_deg = self.shoulder_deg
            e_deg = self.elbow_deg
            g_deg = self.gripper_deg

        # Kinematic calculations:
        # Base: 0° (Right) to 180° (Left), 90° center -> yaw radians
        yaw_base = (b_deg - 90.0) * (math.pi / 180.0)
        
        # Shoulder: 0° to 180° -> pitch radians around Y
        pitch_shoulder = s_deg * (math.pi / 180.0)
        
        # Elbow: 0° to 180° -> pitch radians around Y
        pitch_elbow = e_deg * (math.pi / 180.0)
        
        # Gripper: 90° (Closed) to 270° (Wide open) -> claw angular spread
        open_frac = max(0.0, min(1.0, (g_deg - 90.0) / 180.0))
        claw_angle = open_frac * 0.6  # Radians

        # 1. Publish JointState message
        js = JointState()
        js.header.stamp = now
        js.name = [
            'base_joint',
            'shoulder_joint',
            'elbow_joint',
            'gripper_left_joint',
            'gripper_right_joint'
        ]
        js.position = [
            float(yaw_base),
            float(pitch_shoulder),
            float(pitch_elbow),
            float(claw_angle),
            float(claw_angle)
        ]
        self.joint_pub.publish(js)

        # 2. Broadcast Live Dynamic Arm TF Transforms
        dyn_tfs = []

        # arm_mount -> arm_base_link (Base Yaw rotation)
        t_base = TransformStamped()
        t_base.header.stamp = now
        t_base.header.frame_id = 'arm_mount'
        t_base.child_frame_id = 'arm_base_link'
        t_base.transform.translation.z = 0.015
        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, yaw_base)
        t_base.transform.rotation.x = qx
        t_base.transform.rotation.y = qy
        t_base.transform.rotation.z = qz
        t_base.transform.rotation.w = qw
        dyn_tfs.append(t_base)

        # arm_base_link -> arm_shoulder_link (Shoulder Pitch rotation)
        t_sh = TransformStamped()
        t_sh.header.stamp = now
        t_sh.header.frame_id = 'arm_base_link'
        t_sh.child_frame_id = 'arm_shoulder_link'
        t_sh.transform.translation.z = 0.03
        qx, qy, qz, qw = euler_to_quaternion(0.0, pitch_shoulder, 0.0)
        t_sh.transform.rotation.x = qx
        t_sh.transform.rotation.y = qy
        t_sh.transform.rotation.z = qz
        t_sh.transform.rotation.w = qw
        dyn_tfs.append(t_sh)

        # arm_shoulder_link -> arm_elbow_link (Elbow Pitch rotation)
        t_el = TransformStamped()
        t_el.header.stamp = now
        t_el.header.frame_id = 'arm_shoulder_link'
        t_el.child_frame_id = 'arm_elbow_link'
        t_el.transform.translation.z = 0.10
        qx, qy, qz, qw = euler_to_quaternion(0.0, pitch_elbow, 0.0)
        t_el.transform.rotation.x = qx
        t_el.transform.rotation.y = qy
        t_el.transform.rotation.z = qz
        t_el.transform.rotation.w = qw
        dyn_tfs.append(t_el)

        # arm_wrist_link -> arm_left_claw
        t_lc = TransformStamped()
        t_lc.header.stamp = now
        t_lc.header.frame_id = 'arm_wrist_link'
        t_lc.child_frame_id = 'arm_left_claw'
        t_lc.transform.translation.x = 0.025
        t_lc.transform.translation.y = 0.015
        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, claw_angle)
        t_lc.transform.rotation.x = qx
        t_lc.transform.rotation.y = qy
        t_lc.transform.rotation.z = qz
        t_lc.transform.rotation.w = qw
        dyn_tfs.append(t_lc)

        # arm_wrist_link -> arm_right_claw
        t_rc = TransformStamped()
        t_rc.header.stamp = now
        t_rc.header.frame_id = 'arm_wrist_link'
        t_rc.child_frame_id = 'arm_right_claw'
        t_rc.transform.translation.x = 0.025
        t_rc.transform.translation.y = -0.015
        qx, qy, qz, qw = euler_to_quaternion(0.0, 0.0, -claw_angle)
        t_rc.transform.rotation.x = qx
        t_rc.transform.rotation.y = qy
        t_rc.transform.rotation.z = qz
        t_rc.transform.rotation.w = qw
        dyn_tfs.append(t_rc)

        self.tf_broadcaster.sendTransform(dyn_tfs)

    def destroy_node(self):
        self.running = False
        super().destroy_node()

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
