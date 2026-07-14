#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import math

class ObstacleAvoidanceNode(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')
        
        # 1. Subscribe to the Lidar scan data
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        self.get_logger().info('Obstacle Avoidance Node started. Listening to /scan')
        
        # 2. Publisher for escape velocity commands
        # This publishes a Twist message with the recommended turn speed if blocked
        self.publisher_ = self.create_publisher(Twist, '/obstacle_avoidance/cmd_vel', 10)
        
        # Settings
        self.safe_distance = 0.4 # meters
        
    def scan_callback(self, msg):
        """
        Processes the raw LaserScan message.
        """
        # Calculate the angle of each measurement
        # LaserScan msg contains ranges[], angle_min, angle_max, angle_increment
        
        min_range = float('inf')
        closest_angle = 0.0
        
        # Iterate over all ranges in the scan
        for i, r in enumerate(msg.ranges):
            # Ignore infinite or zero readings (invalid data)
            if math.isinf(r) or math.isnan(r) or r < 0.1:
                continue
                
            # Calculate the actual angle in radians
            angle_rad = msg.angle_min + i * msg.angle_increment
            
            # Convert to degrees for easier logic (-180 to 180)
            angle_deg = math.degrees(angle_rad)
            
            # We only care about obstacles directly in front of the robot (-90 to +90 degrees)
            if -90 <= angle_deg <= 90:
                if r < min_range:
                    min_range = r
                    closest_angle = angle_deg
                    
        cmd_msg = Twist()
        
        # If an obstacle is too close, calculate escape velocity
        if min_range < self.safe_distance:
            self.get_logger().warn(f"OBSTACLE DETECTED! Distance: {min_range:.2f}m at {closest_angle:.1f} deg")
            
            # Stop moving forward
            cmd_msg.linear.x = 0.0
            
            # Steer away from the obstacle
            if closest_angle < 0:
                cmd_msg.angular.z = 1.0  # Turn Left
            else:
                cmd_msg.angular.z = -1.0 # Turn Right
        else:
            # Path is clear, no override needed
            cmd_msg.linear.x = 0.0
            cmd_msg.angular.z = 0.0
            
        self.publisher_.publish(cmd_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidanceNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
