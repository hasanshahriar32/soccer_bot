import os

path = '/home/sharmin/Desktop/iot/soccer_bot/src/ydlidar_ros2_driver/src/ydlidar_ros2_driver_node.cpp'
with open(path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'declare_parameter' in line and '//' not in line:
        new_lines.append('// ' + line)
    else:
        new_lines.append(line)

with open(path, 'w') as f:
    f.writelines(new_lines)
print("Patched ALL declare_parameter calls.")
