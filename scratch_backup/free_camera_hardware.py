import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

print("1. Freeing Pi Camera hardware /dev/video0...")
client.exec_command("sudo killall -9 rpicam-vid python3 python ; docker stop soccer_bot_edge")
time.sleep(2)

print("2. Starting Picamera2 Server on port 8080...")
client.exec_command("nohup python3 ~/picam_server.py > ~/camera.log 2>&1 &")
time.sleep(3)

s, o, e = client.exec_command("cat ~/camera.log")
print("Picamera2 Server Log:\n", o.read().decode())
client.close()
