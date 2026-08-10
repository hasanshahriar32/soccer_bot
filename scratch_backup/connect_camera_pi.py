import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

camera_script = """#!/bin/bash
pkill -f rpicam-vid
while true; do
    rpicam-vid -t 0 --inline -o tcp://192.168.0.112:8000 --codec mjpeg --width 640 --height 480 --framerate 15 >> ~/camera.log 2>&1
    sleep 1
done
"""

client.exec_command("cat << 'EOF' > ~/start_camera.sh\n" + camera_script + "\nEOF\nchmod +x ~/start_camera.sh")
time.sleep(1)

client.exec_command("pkill -f rpicam-vid")
time.sleep(1)

client.exec_command("nohup ~/start_camera.sh > /dev/null 2>&1 &")
time.sleep(2)

s, o, e = client.exec_command("ps aux | grep rpicam")
print("Camera process on Pi:\n", o.read().decode())
client.close()
