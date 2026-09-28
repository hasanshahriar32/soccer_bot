import paramiko
import time

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 65)
    print("        DEEP ARDUINO & MOTOR HARDWARE DIAGNOSIS")
    print("=" * 65)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)

    # 1. Check Serial Ports
    print("\n[1] Connected USB/Serial Ports on Pi:")
    stdin, stdout, stderr = ssh.exec_command("ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null")
    print(stdout.read().decode().strip())

    # 2. Check who is using /dev/ttyACM0
    print("\n[2] Processes using /dev/ttyACM0:")
    stdin, stdout, stderr = ssh.exec_command("fuser /dev/ttyACM0 2>/dev/null || echo 'No process locking /dev/ttyACM0'")
    print(stdout.read().decode().strip())

    # 3. Direct Serial Communication Test with Arduino
    print("\n[3] Direct Serial Test to Arduino Uno (/dev/ttyACM0 @ 9600 Baud):")
    py_test = """
import serial
import time

try:
    s = serial.Serial('/dev/ttyACM0', 9600, timeout=2.0)
    time.sleep(2.0) # Wait for Arduino bootloader reset
    print('Serial Port Opened! Sending FORWARD (F)...')
    s.write(b'F\\n')
    time.sleep(1.0)
    
    # Read response
    resp = s.read(s.in_waiting or 100).decode('utf-8', errors='ignore')
    print(f'Arduino Response: {resp.strip()}')
    
    time.sleep(2.0)
    print('Sending STOP (S)...')
    s.write(b'S\\n')
    s.close()
    print('Direct Serial Test Complete!')
except Exception as e:
    print(f'Serial Error: {e}')
"""
    stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{py_test}\"")
    print(stdout.read().decode().strip())
    print(stderr.read().decode().strip())

    # 4. Check Arduino CLI or Avrdude availability on Pi
    print("\n[4] Checking Arduino Flasher Tool (arduino-cli / avrdude):")
    stdin, stdout, stderr = ssh.exec_command("which arduino-cli avrdude 2>/dev/null || echo 'None installed'")
    print(stdout.read().decode().strip())

    ssh.close()
    print("\n" + "=" * 65)

if __name__ == '__main__':
    main()
