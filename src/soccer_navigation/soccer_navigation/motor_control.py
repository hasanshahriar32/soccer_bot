#!/usr/bin/env python3
"""
====================================================================
         ROS 2 → ARDUINO MOTOR BRIDGE (SERIAL PWM CONTROL)
====================================================================
Description:
    Subscribes to /cmd_vel (Twist), converts to differential drive
    PWM values, and sends "L:{pwm} R:{pwm}\n" over USB serial to
    the Arduino motor driver.

    Runs on the Raspberry Pi (connected to Arduino via /dev/ttyACM0).

Protocol:
    TX format: "L:{-255..255} R:{-255..255}\n"
    Baud rate: 115200
    Keepalive: Sends "L:0 R:0\n" every 400ms if no cmd_vel received
               (prevents Arduino watchdog timeout)
====================================================================
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import serial.tools.list_ports
import time
import os

# Serial settings
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1.0

# Motor scaling
MAX_PWM = 220          # Max PWM output (leave headroom from 255)
WHEEL_BASE = 0.21      # Distance between wheels in meters


class MotorController(Node):
    def __init__(self):
        super().__init__('motor_controller')

        self.subscription = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)

        # Auto-detect Arduino serial port
        self.ser = None
        port = self.find_arduino_port()
        if port:
            self.get_logger().info(f"Connecting to Arduino on {port} @ {BAUD_RATE}...")
            try:
                self.ser = serial.Serial(port, BAUD_RATE, timeout=SERIAL_TIMEOUT)
                time.sleep(2.0)  # Wait for Arduino reset
                self.get_logger().info(f"Connected to Arduino on {port}!")
            except Exception as e:
                self.get_logger().error(f"Failed to open serial port: {e}")
                self.ser = None
        else:
            self.get_logger().warn(
                "No Arduino detected on /dev/ttyACM* or /dev/ttyUSB*. "
                "Motor commands will be logged but not sent.")

        # Keepalive timer (prevent Arduino watchdog timeout)
        self.last_cmd_time = time.time()
        self.keepalive_timer = self.create_timer(0.4, self.keepalive)

    def find_arduino_port(self):
        """Auto-detect Arduino serial port."""
        # Check common Linux paths
        for path in ['/dev/ttyACM0', '/dev/ttyACM1',
                     '/dev/ttyUSB0', '/dev/ttyUSB1']:
            if os.path.exists(path):
                return path

        # Fallback: scan all serial ports
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if 'Arduino' in (p.description or '') or 'ACM' in (p.device or ''):
                return p.device

        return None

    def cmd_vel_callback(self, msg: Twist):
        linear = msg.linear.x
        angular = msg.angular.z

        # Differential drive kinematics
        left_vel = linear - (angular * WHEEL_BASE / 2.0)
        right_vel = linear + (angular * WHEEL_BASE / 2.0)

        # Normalize to [-1.0, 1.0]
        max_val = max(abs(left_vel), abs(right_vel), 0.001)
        if max_val > 1.0:
            left_vel /= max_val
            right_vel /= max_val

        # Scale to PWM range
        pwm_left = int(left_vel * MAX_PWM)
        pwm_right = int(right_vel * MAX_PWM)

        self.send_command(pwm_left, pwm_right)
        self.last_cmd_time = time.time()

    def send_command(self, pwm_left, pwm_right):
        command = f"L:{pwm_left} R:{pwm_right}\n"

        if self.ser and self.ser.is_open:
            try:
                self.ser.write(command.encode('utf-8'))
            except Exception as e:
                self.get_logger().error(f"Serial write error: {e}")

    def keepalive(self):
        """Send stop command if no cmd_vel received recently."""
        if time.time() - self.last_cmd_time > 0.4:
            self.send_command(0, 0)


def main(args=None):
    rclpy.init(args=args)
    controller = MotorController()
    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        pass
    finally:
        if controller.ser and controller.ser.is_open:
            controller.ser.write(b"L:0 R:0\n")
            controller.ser.close()
        controller.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
