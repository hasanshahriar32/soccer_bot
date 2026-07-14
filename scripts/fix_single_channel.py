import os

filepath = '/home/sharmin/Desktop/iot/soccer_bot/src/ydlidar_ros2_driver/src/ydlidar_ros2_driver_node.cpp'

with open(filepath, 'r') as f:
    content = f.read()

# The X4 is a SINGLE CHANNEL lidar, but the C++ file defaults to false and ignores parameters.
# We must hardcode it to true for the X4!
content = content.replace('/// one-way communication\n  b_optvalue = false;', '/// one-way communication\n  b_optvalue = true;')

with open(filepath, 'w') as f:
    f.write(content)

print("Fixed isSingleChannel in C++ code!")
