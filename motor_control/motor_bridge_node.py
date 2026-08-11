import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import time

class MotorBridgeNode(Node):
    def __init__(self):
        super().__init__('motor_bridge_node')
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.port = '/dev/ttyACM0'
        self.baud = 9600
        self.serial_conn = None
        self.last_cmd = 'S'
        
        self.get_logger().info(f"Connecting to Arduino on {self.port} @ {self.baud} baud...")
        try:
            self.serial_conn = serial.Serial(self.port, self.baud, timeout=1.0)
            time.sleep(2.0)
            self.get_logger().info("Connected to Arduino Motor Controller successfully!")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")

    def cmd_vel_callback(self, msg: Twist):
        if not self.serial_conn or not self.serial_conn.is_open:
            return
            
        linear_x = msg.linear.x
        angular_z = msg.angular.z
        
        # Velocity to discrete command mapping
        cmd = 'S'
        if linear_x > 0.05:
            cmd = 'F'
        elif linear_x < -0.05:
            cmd = 'B'
        elif angular_z > 0.1:
            cmd = 'L'
        elif angular_z < -0.1:
            cmd = 'R'
        else:
            cmd = 'S'
            
        if cmd != self.last_cmd:
            try:
                self.serial_conn.write(cmd.encode())
                self.serial_conn.flush()
                self.last_cmd = cmd
                self.get_logger().info(f"Sent command: '{cmd}' (linear_x={linear_x:.2f}, angular_z={angular_z:.2f})")
            except Exception as e:
                self.get_logger().error(f"Serial write error: {e}")

    def destroy_node(self):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(b'S')
                self.serial_conn.close()
            except:
                pass
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
