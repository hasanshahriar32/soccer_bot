import paramiko
import time

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print(f"Connecting to Raspberry Pi ({ip})...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=password, timeout=8)
        print("[SUCCESS] Connected to Raspberry Pi!")
        print("=" * 50)
        
        # 1. System Info
        stdin, stdout, stderr = ssh.exec_command('hostname; uname -a; uptime')
        print(stdout.read().decode().strip())
        print("-" * 50)
        
        # 2. Docker Containers
        stdin, stdout, stderr = ssh.exec_command('docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"')
        print("DOCKER CONTAINERS:")
        print(stdout.read().decode().strip())
        print("-" * 50)
        
        # 3. Active Processes
        stdin, stdout, stderr = ssh.exec_command('pgrep -a python3; pgrep -a rpicam-vid')
        print("ACTIVE ROBOT PROCESSES:")
        print(stdout.read().decode().strip())
        print("=" * 50)
        
        ssh.close()
    except Exception as e:
        print("[ERROR] Failed to connect to Pi:", str(e))

if __name__ == '__main__':
    main()
