#!/usr/bin/env python3
"""
====================================================================
      REAL-TIME 2D OCCUPANCY GRID MAPPER NODE — ROS 2 JAZZY
====================================================================
Description:
    Subscribes to /scan (sensor_msgs/LaserScan) and builds a live 
    2D occupancy grid map published on /map (nav_msgs/OccupancyGrid)
    with TRANSIENT_LOCAL QoS for immediate RViz2 visualization.
====================================================================
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid, MapMetaData
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
import numpy as np
import math
import time

MAP_WIDTH = 200    # 200 cells
MAP_HEIGHT = 200   # 200 cells
RESOLUTION = 0.05  # 5 cm per cell -> 10m x 10m map
ORIGIN_X = -(MAP_WIDTH * RESOLUTION) / 2.0   # -5.0 m
ORIGIN_Y = -(MAP_HEIGHT * RESOLUTION) / 2.0  # -5.0 m

class FastOccupancyMapper(Node):
    def __init__(self):
        super().__init__('fast_occupancy_mapper')
        
        # QoS Profile for Map Topic (TRANSIENT_LOCAL required by RViz2)
        qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )
        
        self.map_pub = self.create_publisher(OccupancyGrid, '/map', qos)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        
        # Initialize map array: -1 = unknown, 0 = free, 100 = occupied
        self.grid = np.full((MAP_HEIGHT, MAP_WIDTH), -1, dtype=np.int8)
        
        # Center robot start cell as free
        cx, cy = MAP_WIDTH // 2, MAP_HEIGHT // 2
        self.grid[cy-2:cy+3, cx-2:cx+3] = 0
        
        # Periodic map publisher (2 Hz)
        self.timer = self.create_timer(0.5, self.publish_map)
        self.last_scan_time = 0.0
        self.get_logger().info("Fast 2D Occupancy Grid Mapper active on /map")

    def scan_callback(self, msg: LaserScan):
        self.last_scan_time = time.time()
        cx = MAP_WIDTH // 2
        cy = MAP_HEIGHT // 2
        
        angle = msg.angle_min
        for r in msg.ranges:
            if msg.range_min <= r <= msg.range_max:
                # Target obstacle cell in grid
                ox = cx + int((r * math.cos(angle)) / RESOLUTION)
                oy = cy + int((r * math.sin(angle)) / RESOLUTION)
                
                # Bresenham ray trace from (cx, cy) to (ox, oy)
                self.ray_trace(cx, cy, ox, oy)
            angle += msg.angle_increment

    def ray_trace(self, x0, y0, x1, y1):
        """Bresenham line algorithm to clear ray and mark obstacle cell."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        while True:
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                if x == x1 and y == y1:
                    # Obstacle hit
                    self.grid[y, x] = 100
                    break
                else:
                    # Free space along ray
                    if self.grid[y, x] != 100:
                        self.grid[y, x] = 0
                        
            if x == x1 and y == y1:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def publish_map(self):
        msg = OccupancyGrid()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        
        msg.info.resolution = float(RESOLUTION)
        msg.info.width = MAP_WIDTH
        msg.info.height = MAP_HEIGHT
        msg.info.origin.position.x = float(ORIGIN_X)
        msg.info.origin.position.y = float(ORIGIN_Y)
        msg.info.origin.position.z = 0.0
        msg.info.origin.orientation.w = 1.0
        
        msg.data = self.grid.flatten().tolist()
        self.map_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = FastOccupancyMapper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
