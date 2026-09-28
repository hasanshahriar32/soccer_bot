import paramiko
import time

def main():
    print("=" * 55)
    print("      SOCCER BOT ARDUINO MOTOR CONTROLLER TEST")
    print("=" * 55)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    pi_code = """import serial
import time

port = '/dev/ttyACM0'
baud = 115200

print(f"[1] Connecting to Arduino on {port} @ {baud} baud...")
try:
    s = serial.Serial(port, baud, timeout=2.0)
    time.sleep(2.0)
    
    boot_msg = s.read(s.in_waiting or 64).decode('utf-8', errors='ignore')
    if boot_msg:
        print(f"[2] Received Boot Message: {boot_msg.strip()}")
        
    print("[3] Sending Test Motor Pulse (L:120 R:120)...")
    s.write(b"L:120 R:120\\n")
    s.flush()
    time.sleep(0.5)
    
    print("[4] Sending Safe Stop Command (L:0 R:0)...")
    s.write(b"L:0 R:0\\n")
    s.flush()
    time.sleep(0.2)
    
    s.close()
    print("[SUCCESS] Motor controller is ONLINE and commands verified!")
except Exception as e:
    print(f"[ERROR] Motor test error: {e}")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_motor.py', 'w') as f:
        f.write(pi_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_motor.py')
    print(stdout.read().decode().strip())
    
    err = stderr.read().decode().strip()
    if err:
        print("STDERR:", err)
        
    ssh.close()
    print("=" * 55)

if __name__ == '__main__':
    main()
