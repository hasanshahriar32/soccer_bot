import paramiko

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=5)
        # Send safe stop to Arduino
        ssh.exec_command('python3 -c "import serial; s = serial.Serial(\'/dev/ttyACM0\', 9600, timeout=1); s.write(b\'S\'); s.close()"')
        ssh.close()
        print("[OK] Motors placed in safe stopped state.")
    except Exception as e:
        print(f"Note: {e}")

if __name__ == '__main__':
    main()
