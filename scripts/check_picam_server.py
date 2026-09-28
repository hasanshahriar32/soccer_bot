import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    stdin, stdout, stderr = ssh.exec_command('cat /home/hasan/picam_server.py 2>/dev/null || head -n 30 /home/hasan/*.py')
    print("--- Pi Camera Script ---")
    print(stdout.read().decode())
    ssh.close()

if __name__ == '__main__':
    main()
