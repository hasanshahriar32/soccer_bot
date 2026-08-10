import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

print("Stopping previous Pi streaming processes...")
client.exec_command("pkill -f python_socat.py ; pkill -f edge_lidar.py ; pkill -f rpicam-vid")
time.sleep(1)

print("Starting Camera server on port 8000...")
client.exec_command("nohup ~/start_camera.sh > /dev/null 2>&1 &")

print("Starting Lidar server (edge_lidar.py) on port 5000...")
client.exec_command("nohup python3 ~/edge_lidar.py > ~/lidar.log 2>&1 &")
time.sleep(2)

s, o, e = client.exec_command("ps aux | grep -E 'rpicam|edge_lidar'")
print("Active Pi processes:\n", o.read().decode())
client.close()
