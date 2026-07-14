import os
import re

filepath = '/home/sharmin/Desktop/iot/soccer_bot/src/ydlidar_ros2_driver/src/ydlidar_ros2_driver_node.cpp'

with open(filepath, 'r') as f:
    content = f.read()

# Hardcode the correct defaults for the Pi directly into the C++ file, so it ignores missing ROS 2 parameter declarations
content = content.replace('std::string str_optvalue = "/tmp/virtual_lidar";', 'std::string str_optvalue = "/dev/ttyUSB0";')
content = content.replace('int optval = 115200;', 'int optval = 115200;') # Already 115200
# Also make sure the motor DTR is True if needed (Wait, standard X4 uses DTR=False in standard configs sometimes, but we know true_probe needed it? Let's leave it false for now, since native C++ SDK does its own power sequence)

with open(filepath, 'w') as f:
    f.write(content)

print("Fixed ydlidar_ros2_driver_node.cpp to default to /dev/ttyUSB0!")
