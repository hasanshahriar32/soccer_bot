import re

path = '/home/sharmin/Desktop/iot/soccer_bot/src/ydlidar_ros2_driver/src/ydlidar_ros2_driver_node.cpp'
with open(path, 'r') as f:
    data = f.read()

# Comment out all declare_parameter lines
data = re.sub(r'(node->declare_parameter\([^;]+;\))', r'// \1', data)

# Change node initialization to allow undeclared parameters
old_init = 'auto node = rclcpp::Node::make_shared("ydlidar_ros2_driver_node");'
new_init = '''rclcpp::NodeOptions options;
  options.allow_undeclared_parameters(true);
  options.automatically_declare_parameters_from_overrides(true);
  auto node = rclcpp::Node::make_shared("ydlidar_ros2_driver_node", options);'''
data = data.replace(old_init, new_init)

with open(path, 'w') as f:
    f.write(data)
print("Patched ydlidar_ros2_driver_node.cpp successfully.")
