import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

cmd = "find / -name '*.urdf*' -o -name '*.xacro*' 2>/dev/null"
s, o, e = client.exec_command(cmd)
print("Found URDF/Xacro files on Pi:\n", o.read().decode())
client.close()
