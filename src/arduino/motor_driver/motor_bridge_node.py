#!/usr/bin/env python3
"""
motor_bridge_node.py
ROS 2 node running on the Raspberry Pi.
Subscribes to /cmd_vel (Twist messages) and translates them
into single-byte serial commands sent to the Arduino Uno via USB.

Topic: /cmd_vel  (geometry_msgs/Twist)
  linear.x  > 0  -> Forward
  linear.x  < 0  -> Backward
  angular.z > 0  -> Turn Left
  angular.z < 0  -> Turn Right
  all zero        -> Stop
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import serial.tools.list_ports


def find_arduino_port():
    """Auto-detect Arduino USB port."""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if 'Arduino' in p.description or 'ttyUSB' in p.device or 'ttyACM' in p.device:
            return p.device
    return None


class MotorBridgeNode(Node):
    def __init__(self):
        super().__init__('motor_bridge_node')

        # --- Find and open Arduino serial port ---
        port = find_arduino_port()
        if port is None:
            port = '/dev/ttyACM0'  # Fallback default
            self.get_logger().warn(f'Arduino not detected, trying fallback: {port}')
        else:
            self.get_logger().info(f'Arduino found at: {port}')

        try:
            self.ser = serial.Serial(port, 9600, timeout=1)
            self.get_logger().info('Serial connection established.')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            self.ser = None

        # --- Subscribe to /cmd_vel ---
        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.last_cmd = 'S'
        self.get_logger().info('Motor Bridge Node started. Listening on /cmd_vel')

    def cmd_vel_callback(self, msg: Twist):
        lin = msg.linear.x
        ang = msg.angular.z

        # Determine command
        if abs(lin) < 0.01 and abs(ang) < 0.01:
            cmd = 'S'  # Stop
        elif lin > 0:
            cmd = 'F'  # Forward
        elif lin < 0:
            cmd = 'B'  # Backward
        elif ang > 0:
            cmd = 'L'  # Turn Left
        elif ang < 0:
            cmd = 'R'  # Turn Right
        else:
            cmd = 'S'

        # Only send if command changed (avoid serial flooding)
        if cmd != self.last_cmd:
            self.last_cmd = cmd
            self.send_command(cmd)

    def send_command(self, cmd: str):
        if self.ser and self.ser.is_open:
            self.ser.write(cmd.encode())
            self.get_logger().info(f'Sent motor command: {cmd}')
        else:
            self.get_logger().warn('Serial port not open — cannot send command.')

    def destroy_node(self):
        # Always stop motors cleanly on shutdown
        self.send_command('S')
        if self.ser:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
