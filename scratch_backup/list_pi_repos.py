import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

cmd = "ls -la ~/soccer_bot/ ; docker images"
s, o, e = client.exec_command(cmd)
print("Files and Docker images on Pi:\n", o.read().decode())
client.close()
