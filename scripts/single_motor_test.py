import paramiko
import time
import sys

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 65)
    print("         ISOLATED SINGLE MOTOR DIAGNOSTIC TEST")
    print("=" * 65)
    print(f"Connecting to Raspberry Pi ({PI_IP})...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=6)
        print("[1] SSH Connected to Pi!")
    except Exception as e:
        print(f"[FAIL] Could not connect: {e}")
        return

    # Python runner on the Pi to test Left and Right motors individually
    pi_code = """import serial, time
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    time.sleep(2.0)

    # 1. LEFT MOTOR ONLY (PWM on Left = 240, Right = 0)
    print('\\n>>> [TEST 1/2] SPINNING LEFT MOTOR ONLY (3 Seconds)...')
    start = time.time()
    while time.time() - start < 3.0:
        ser.write(b'L:240 R:0\\n')
        ser.flush()
        time.sleep(0.04)

    # Stop
    ser.write(b'L:0 R:0\\n')
    ser.flush()
    time.sleep(1.5)

    # 2. RIGHT MOTOR ONLY (PWM on Left = 0, Right = 240)
    print('>>> [TEST 2/2] SPINNING RIGHT MOTOR ONLY (3 Seconds)...')
    start = time.time()
    while time.time() - start < 3.0:
        ser.write(b'L:0 R:240\\n')
        ser.flush()
        time.sleep(0.04)

    # Stop
    ser.write(b'L:0 R:0\\n')
    ser.flush()
    ser.close()
    print('\\n>>> [SINGLE MOTOR TEST COMPLETED]!')
except Exception as err:
    print('Serial Error:', err)
"""
    # Temporarily stop background service for exclusive port access
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl stop soccer_motor.service")
    time.sleep(1.0)

    print("\n[2] Starting Isolated Single Motor Test...")
    stdin, stdout, stderr = ssh.exec_command(f"python3 -u -c \"{pi_code}\"")
    print(stdout.read().decode().strip())

    # Re-enable service
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl start soccer_motor.service")
    ssh.close()

    print("\n" + "=" * 65)

if __name__ == '__main__':
    main()
