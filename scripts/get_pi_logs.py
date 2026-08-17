import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
        stdin, stdout, stderr = ssh.exec_command('vcgencmd get_throttled ; echo "=== DMESG ===" ; dmesg | tail -n 25')
        print(stdout.read().decode('utf-8', errors='ignore'))
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
