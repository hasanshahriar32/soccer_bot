import paramiko
import time

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("        SOCCER BOT - AUTOMATED MOTOR TEST SUITE")
    print("=" * 60)
    
    print(f"Connecting to Raspberry Pi ({PI_IP})...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
    
    pi_script = """import serial, time

port = '/dev/ttyACM0'
baud = 9600

s = serial.Serial(port, baud, timeout=1.0)
time.sleep(2.0)

tests = [
    ('F', 'FORWARD', 1.5),
    ('S', 'STOP', 0.5),
    ('B', 'BACKWARD', 1.5),
    ('S', 'STOP', 0.5),
    ('L', 'TURN LEFT', 1.0),
    ('S', 'STOP', 0.5),
    ('R', 'TURN RIGHT', 1.0),
    ('S', 'STOP', 0.5)
]

for cmd, desc, dur in tests:
    print(f">> Executing: {desc} (Command: '{cmd}') for {dur}s...")
    s.write(cmd.encode())
    s.flush()
    time.sleep(dur)

s.close()
print("All motor tests completed successfully!")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/auto_test_motors.py', 'w') as f:
        f.write(pi_script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/auto_test_motors.py')
    print(stdout.read().decode().strip())
    
    ssh.close()
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
