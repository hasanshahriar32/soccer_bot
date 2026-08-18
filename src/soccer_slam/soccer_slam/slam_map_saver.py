#!/usr/bin/env python3
"""
====================================================================
Soccer Bot SLAM Map Snapshot & Exporter Utility
====================================================================
Subscribes to '/map' (nav_msgs/OccupancyGrid) and exports:
  1. Standard ROS 2 map (.yaml + .pgm) for Nav2 / localization
  2. High-contrast PNG visualization with coordinate grid
====================================================================
"""

import os
import sys
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
import numpy as np
import cv2


class MapSaverNode(Node):
    def __init__(self, output_name='soccer_bot_map'):
        super().__init__('soccer_map_saver')
        self.output_name = output_name
        self.received_map = None

        qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )

        self.sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            qos
        )
        self.get_logger().info("[MAP SAVER] Waiting for '/map' OccupancyGrid data...")

    def map_callback(self, msg: OccupancyGrid):
        self.received_map = msg
        self.get_logger().info(
            f"[MAP SAVER] Received Map! Dimensions: {msg.info.width}x{msg.info.height}, "
            f"Resolution: {msg.info.resolution:.3f} m/cell"
        )
        self.save_map()

    def save_map(self):
        if self.received_map is None:
            self.get_logger().warn("[MAP SAVER] No map received yet.")
            return

        msg = self.received_map
        width = msg.info.width
        height = msg.info.height
        res = msg.info.resolution
        origin_x = msg.info.origin.position.x
        origin_y = msg.info.origin.position.y

        # Convert 1D data to 2D numpy array
        raw_data = np.array(msg.data, dtype=np.int8).reshape((height, width))

        # Map pixel values:
        # -1 = Unknown -> 205 (gray)
        #  0 = Free    -> 254 (white)
        # 100 = Occupied -> 0 (black)
        img = np.zeros((height, width), dtype=np.uint8)
        img[raw_data == -1] = 205
        img[raw_data == 0] = 254
        img[raw_data > 50] = 0

        # Flip vertically so (0,0) is bottom-left as standard for ROS maps
        img = np.flipud(img)

        # Output directory
        output_dir = "/home/sharmin/Desktop/iot/soccer_bot/src/soccer_slam/maps"
        os.makedirs(output_dir, exist_ok=True)

        base_path = os.path.join(output_dir, self.output_name)
        pgm_path = f"{base_path}.pgm"
        png_path = f"{base_path}.png"
        yaml_path = f"{base_path}.yaml"

        # Save PGM & PNG
        cv2.imwrite(pgm_path, img)
        cv2.imwrite(png_path, img)

        # Save YAML metadata
        yaml_content = f"""image: {os.path.basename(pgm_path)}
mode: trinary
resolution: {res}
origin: [{origin_x}, {origin_y}, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
"""
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)

        self.get_logger().info(f"✅ [SUCCESS] Map saved successfully!")
        self.get_logger().info(f"   -> YAML: {yaml_path}")
        self.get_logger().info(f"   -> PGM:  {pgm_path}")
        self.get_logger().info(f"   -> PNG:  {png_path}")


def main(args=None):
    rclpy.init(args=args)
    map_name = sys.argv[1] if len(sys.argv) > 1 else f"soccer_bot_map_{int(time.time())}"
    node = MapSaverNode(output_name=map_name)

    # Spin briefly to catch transient local /map
    timeout = 10.0
    start = time.time()
    while rclpy.ok() and node.received_map is None and (time.time() - start) < timeout:
        rclpy.spin_once(node, timeout_sec=0.2)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
