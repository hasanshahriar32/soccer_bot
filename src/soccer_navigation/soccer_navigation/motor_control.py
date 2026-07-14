import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import time

class MotorController(Node):
    def __init__(self):
        super().__init__('motor_controller')
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10)
            
        # Connect to Arduino over USB Serial
        self.arduino_port = '/dev/ttyACM0'  # Might be /dev/ttyUSB1 depending on the Arduino model
        self.baudrate = 115200
        
        self.get_logger().info(f"Connecting to Arduino on {self.arduino_port}...")
        try:
            self.ser = serial.Serial(self.arduino_port, self.baudrate, timeout=1.0)
            time.sleep(2) # Wait for Arduino to reset
            self.get_logger().info("Connected to Arduino!")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")
            self.ser = None

    def cmd_vel_callback(self, msg):
        if not self.ser:
            return
            
        linear_x = msg.linear.x
        angular_z = msg.angular.z
        
        # Differential drive kinematic conversion
        left_speed = linear_x - angular_z
        right_speed = linear_x + angular_z
        
        # Normalize speeds to be between -1.0 and 1.0
        max_speed = max(abs(left_speed), abs(right_speed), 1.0)
        left_speed /= max_speed
        right_speed /= max_speed
        
        # Scale to Arduino PWM (0 to 255)
        pwm_left = int(left_speed * 255)
        pwm_right = int(right_speed * 255)
        
        # Send command to Arduino
        command = f"L:{pwm_left} R:{pwm_right}\n"
        self.ser.write(command.encode('utf-8'))
        # self.get_logger().info(f"Sent: {command.strip()}")

def main(args=None):
    rclpy.init(args=args)
    motor_controller = MotorController()
    try:
        rclpy.spin(motor_controller)
    except KeyboardInterrupt:
        pass
    finally:
        if motor_controller.ser:
            motor_controller.ser.write(b"L:0 R:0\n")
            motor_controller.ser.close()
        motor_controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
