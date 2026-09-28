import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    print("=== SERIAL PORTS (/dev/ttyACM / /dev/ttyUSB) ===")
    stdin, stdout, stderr = ssh.exec_command('ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || echo "No serial devices detected"')
    print(stdout.read().decode())
    
    print("=== CONNECTED USB HARDWARE (lsusb) ===")
    stdin, stdout, stderr = ssh.exec_command('lsusb')
    print(stdout.read().decode())
    
    print("=== CAMERA HARDWARE CHECK ===")
    stdin, stdout, stderr = ssh.exec_command('rpicam-hello --list-cameras 2>/dev/null || echo "libcamera check done"')
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == '__main__':
    main()
