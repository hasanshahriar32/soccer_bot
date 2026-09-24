import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('10.127.69.146', username='hasan', password='grammarpro', timeout=8)
    
    print("=== CAMERA SERVER LOG ===")
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/camera_server.log')
    print(stdout.read().decode())
    
    print("=== LIDAR BRIDGE LOG ===")
    stdin, stdout, stderr = ssh.exec_command('docker exec soccer_bot_edge cat /tmp/lidar_bridge.log')
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == '__main__':
    main()
