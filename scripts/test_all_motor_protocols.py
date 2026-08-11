import paramiko
import time

def main():
    print("=" * 60)
    print("     TESTING ARDUINO MOTOR COMMANDS (9600 & 115200)")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    pi_code = """import serial
import time

port = '/dev/ttyACM0'

# Test Protocol 1: Character Commands at 9600 Baud ('F', 'B', 'S')
print("--- [TEST 1] Testing 9600 Baud Protocol ('F' / 'B' / 'S') ---")
try:
    s = serial.Serial(port, 9600, timeout=1.5)
    time.sleep(2.0)
    
    # Read boot msg
    boot = s.read(s.in_waiting or 64).decode('utf-8', errors='ignore')
    if boot: print(f"  Arduino Response: {boot.strip()}")
    
    print("  -> Sending 'F' (FORWARD) for 2.5 seconds...")
    s.write(b"F")
    s.flush()
    time.sleep(0.1)
    resp = s.read(s.in_waiting or 32).decode('utf-8', errors='ignore')
    if resp: print(f"  Arduino Response: {resp.strip()}")
    time.sleep(2.5)
    
    print("  -> Sending 'S' (STOP)...")
    s.write(b"S")
    s.flush()
    time.sleep(0.5)
    s.close()
    print("  [OK] Test 1 Complete.")
except Exception as e:
    print(f"  Test 1 Note: {e}")

time.sleep(1.0)

# Test Protocol 2: PWM String Commands at 115200 Baud ("L:255 R:255\\n")
print("\\n--- [TEST 2] Testing 115200 Baud Protocol (L:255 R:255) ---")
try:
    s = serial.Serial(port, 115200, timeout=1.5)
    time.sleep(2.0)
    
    boot = s.read(s.in_waiting or 64).decode('utf-8', errors='ignore')
    if boot: print(f"  Arduino Response: {boot.strip()}")
    
    print("  -> Sending 'L:255 R:255\\n' (MAX FORWARD) for 2.5 seconds...")
    s.write(b"L:255 R:255\\n")
    s.flush()
    time.sleep(2.5)
    
    print("  -> Sending 'L:0 R:0\\n' (STOP)...")
    s.write(b"L:0 R:0\\n")
    s.flush()
    time.sleep(0.5)
    s.close()
    print("  [OK] Test 2 Complete.")
except Exception as e:
    print(f"  Test 2 Note: {e}")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_all_protocols.py', 'w') as f:
        f.write(pi_code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/test_all_protocols.py')
    print(stdout.read().decode().strip())
    
    err = stderr.read().decode().strip()
    if err:
        print("STDERR:", err)
        
    ssh.close()
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
