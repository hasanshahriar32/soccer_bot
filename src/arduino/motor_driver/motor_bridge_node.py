#!/usr/bin/env python3
"""
motor_bridge_node.py
ROS 2 node running on the laptop (ROS 2 Jazzy).
Subscribes to /cmd_vel (geometry_msgs/Twist) and sends commands
over TCP socket to motor_edge_server running on the Raspberry Pi (192.168.0.135:6000).

Commands:
  linear.x  >  0.01 -> 'F' (Forward)
  linear.x  < -0.01 -> 'B' (Backward)
  angular.z >  0.01 -> 'L' (Turn Left)
  angular.z < -0.01 -> 'R' (Turn Right)
  otherwise         -> 'S' (Stop)
"""

import socket
import sys
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

PI_IP = '192.168.0.135'
PI_PORT = 6000


class MotorBridgeNode(Node):
    def __init__(self):
        super().__init__('motor_bridge_node')
        self.sock = None
        self.last_cmd = None
        self.connect_to_pi()

        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.get_logger().info('Motor Bridge Node started. Subscribed to /cmd_vel')

    def connect_to_pi(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((PI_IP, PI_PORT))
            self.get_logger().info(f'Successfully connected to Pi Motor Server at {PI_IP}:{PI_PORT}')
        except Exception as e:
            self.get_logger().warn(f'Could not connect to Pi Motor Server: {e}')
            self.sock = None

    def cmd_vel_callback(self, msg: Twist):
        lin = msg.linear.x
        ang = msg.angular.z

        if lin > 0.01:
            cmd = 'F'
        elif lin < -0.01:
            cmd = 'B'
        elif ang > 0.01:
            cmd = 'L'
        elif ang < -0.01:
            cmd = 'R'
        else:
            cmd = 'S'

        if cmd != self.last_cmd:
            self.last_cmd = cmd
            self.send_cmd(cmd)

    def send_cmd(self, cmd: str):
        if not self.sock:
            self.connect_to_pi()

        if self.sock:
            try:
                self.sock.sendall(cmd.encode('utf-8'))
                self.get_logger().info(f'Published /cmd_vel -> Motor Cmd: {cmd}')
            except Exception as e:
                self.get_logger().error(f'Failed to send command over socket: {e}')
                self.sock = None

    def destroy_node(self):
        self.send_cmd('S')
        if self.sock:
            self.sock.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        node.get_logger().info(f'Node shutdown: {e}')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
