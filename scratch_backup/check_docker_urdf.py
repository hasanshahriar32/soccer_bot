import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

cmd = "docker exec $(docker ps -q | head -n 1) ros2 topic list 2>/dev/null ; find / -name '*.urdf' -o -name '*.xacro' 2>/dev/null"
s, o, e = client.exec_command(cmd)
print("Docker ROS 2 Topics and URDF files:\n", o.read().decode())
client.close()
