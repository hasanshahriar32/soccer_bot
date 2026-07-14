import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Point

class CoreBrain(Node):
    def __init__(self):
        super().__init__('core_brain')
        
        # Subscribe to the vision system to get the ball's X, Y coordinates
        self.subscription = self.create_subscription(
            Point,
            '/ball_position',
            self.ball_callback,
            10)
            
        # Publish velocity commands to the motor controller
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Robot physical parameters
        self.target_x_center = 320 / 2.0  # Assuming 320x240 camera resolution
        self.x_tolerance = 30.0  # pixels
        self.y_stop_distance = 200.0  # pixels (how big/close the ball is before we stop)
        
        self.get_logger().info("Core Brain initialized. Waiting for /ball_position...")

    def ball_callback(self, msg):
        ball_x = msg.x
        ball_y = msg.y
        ball_radius = msg.z  # We are using 'z' to pass the radius of the ball
        
        cmd = Twist()
        
        if ball_x < 0:
            # Ball is not visible! Spin in place to search for it.
            cmd.angular.z = 0.5
            cmd.linear.x = 0.0
            self.get_logger().info("Searching for ball...")
        else:
            # We see the ball!
            # 1. Steer left or right to center the ball
            error_x = self.target_x_center - ball_x
            
            if abs(error_x) > self.x_tolerance:
                # Proportional control for steering
                cmd.angular.z = error_x * 0.005 
            else:
                cmd.angular.z = 0.0
                
            # 2. Drive forward if the ball is far away
            if ball_radius < self.y_stop_distance:
                # Move forward proportionally to how far the ball is
                cmd.linear.x = 0.5
            else:
                # Stop if we are right on top of the ball
                cmd.linear.x = 0.0
                
            self.get_logger().info(f"Tracking ball: error_x={error_x:.1f}, linear={cmd.linear.x:.2f}, angular={cmd.angular.z:.2f}")

        self.publisher_.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    core_brain = CoreBrain()
    rclpy.spin(core_brain)
    core_brain.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
