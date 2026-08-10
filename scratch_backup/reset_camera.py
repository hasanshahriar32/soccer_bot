import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

print("1. Killing all background camera wrapper loops...")
client.exec_command("sudo killall -9 start_camera.sh rpicam-vid python3 ; docker stop soccer_bot_edge")
time.sleep(2)

print("2. Starting Flask HTTP Camera Server on port 8080...")
client.exec_command("nohup python3 ~/http_camera_server.py > ~/camera.log 2>&1 &")
time.sleep(3)

s, o, e = client.exec_command("cat ~/camera.log")
print("Camera Log Output:\n", o.read().decode())
client.close()
