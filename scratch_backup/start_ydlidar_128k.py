import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

print("Killing existing Lidar processes...")
client.exec_command("sudo killall -9 ydlidar_ros2_driver_node python3")
time.sleep(1)

run_cmd = """#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash
/ros2_ws/install/ydlidar_ros2_driver/lib/ydlidar_ros2_driver/ydlidar_ros2_driver_node --ros-args -p port:=/dev/ttyUSB0 -p frame_id:=laser_frame -p baudrate:=128000 -p resolution_fixed:=true -p auto_reconnect:=true -p singlechannel:=true >> ~/ydlidar.log 2>&1
"""

client.exec_command("cat << 'EOF' > ~/start_ydlidar.sh\n" + run_cmd + "\nEOF\nchmod +x ~/start_ydlidar.sh")
time.sleep(1)

print("Starting YDLidar ROS 2 Driver at 128000 baud...")
client.exec_command("nohup ~/start_ydlidar.sh > /dev/null 2>&1 &")
time.sleep(4)

s, o, e = client.exec_command("cat ~/ydlidar.log")
print("YDLidar log:\n", o.read().decode())
client.close()
