import paramiko
import time

def main():
    print("=" * 55)
    print("        RUNNING SOCCER BOT MOTOR WHEELS")
    print("=" * 55)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    script = """import serial
import time

port = '/dev/ttyACM0'
baud = 115200

print(f"Connecting to Arduino on {port}...")
s = serial.Serial(port, baud, timeout=1.0)
time.sleep(2.0) # Wait for reset

print(">>> [1/3] Spinning Wheels FORWARD (Speed: 180 / 255)...")
s.write(b"L:180 R:180\\n")
s.flush()
time.sleep(2.0)

print(">>> [2/3] Spinning Wheels REVERSE (Speed: -150 / 255)...")
s.write(b"L:-150 R:-150\\n")
s.flush()
time.sleep(1.5)

print(">>> [3/3] STOPPING MOTORS (L:0 R:0)...")
s.write(b"L:0 R:0\\n")
s.flush()
time.sleep(0.5)

s.close()
print("Wheel test sequence completed safely!")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/spin_wheels.py', 'w') as f:
        f.write(script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/spin_wheels.py')
    print(stdout.read().decode().strip())
    
    err = stderr.read().decode().strip()
    if err:
        print("STDERR:", err)
        
    ssh.close()
    print("=" * 55)

if __name__ == '__main__':
    main()
