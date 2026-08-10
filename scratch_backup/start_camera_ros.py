import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

print("Stopping previous camera processes...")
client.exec_command("pkill -f rpicam-vid ; pkill -f pi_camera_ros.py")
time.sleep(1)

run_cmd = """#!/bin/bash
source /opt/ros/jazzy/setup.bash
python3 ~/soccer_bot/scripts/pi_camera_ros.py >> ~/camera.log 2>&1
"""

client.exec_command("cat << 'EOF' > ~/start_camera_ros.sh\n" + run_cmd + "\nEOF\nchmod +x ~/start_camera_ros.sh")
time.sleep(1)

print("Starting pi_camera_ros.py...")
client.exec_command("nohup ~/start_camera_ros.sh > /dev/null 2>&1 &")
time.sleep(3)

s, o, e = client.exec_command("cat ~/camera.log")
print("Camera log output:\n", o.read().decode())
client.close()
