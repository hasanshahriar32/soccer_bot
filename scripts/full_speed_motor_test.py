import paramiko
import time

def main():
    print("=" * 60)
    print("       SOCCER BOT MOTOR & POWER DIAGNOSTIC TEST")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    script = """import serial
import time

port = '/dev/ttyACM0'
baud = 115200

print(f"[1] Connecting to Arduino on {port}...")
s = serial.Serial(port, baud, timeout=1.0)
time.sleep(2.0)

print("[2] Sending MAXIMUM SPEED FORWARD (L:255 R:255) for 3 seconds...")
for i in range(15):
    s.write(b"L:255 R:255\\n")
    s.flush()
    time.sleep(0.2)

print("[3] Stopping motors...")
s.write(b"L:0 R:0\\n")
s.flush()
time.sleep(0.5)

s.close()
print("[4] Command completed.")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/full_motor_test.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/full_motor_test.py')
    print(stdout.read().decode().strip())
    
    ssh.close()
    print("=" * 60)

if __name__ == '__main__':
    main()
