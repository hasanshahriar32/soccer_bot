import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    print("=== MOTOR SERVER LOG ===")
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/motor_server.log')
    print(stdout.read().decode())
    
    print("=== PROCESSES & PORTS ===")
    stdin, stdout, stderr = ssh.exec_command('ps aux | grep motor_server | grep -v grep ; netstat -tlpn 2>/dev/null | grep 9000')
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == '__main__':
    main()
