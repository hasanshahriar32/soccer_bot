import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

print("1. Stopping old processes on Pi...")
client.exec_command("pkill -9 -f python_socat.py ; pkill -9 -f picam_server.py")
time.sleep(1)

print("2. Starting Lidar Server (port 5000) & Camera Server (port 8080) simultaneously...")
client.exec_command("nohup python3 ~/python_socat.py > ~/socat.log 2>&1 &")
client.exec_command("nohup python3 ~/picam_server.py > ~/camera.log 2>&1 &")
time.sleep(3)

s, o, e = client.exec_command("ps aux | grep -E 'python_socat|picam_server'")
print("Active Pi Sensor Processes:\n", o.read().decode())
client.close()
