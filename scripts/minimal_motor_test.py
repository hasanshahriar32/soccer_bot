import paramiko
import time
import sys

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("        MINIMAL MOTOR SPIN TEST (5 SECONDS FORWARD)")
    print("=" * 60)
    print(f"Connecting to Raspberry Pi ({PI_IP})...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=6)
        print("[1] Connected to Pi!")
    except Exception as e:
        print(f"[FAIL] Could not connect to Pi: {e}")
        return

    # Direct 5-second Python runner on the Pi
    pi_code = """import serial, time
try:
    s = serial.Serial('/dev/ttyACM0', 9600, timeout=1.0)
    time.sleep(2.0)
    print('>>> [ARDUINO READY] Driving Motors FORWARD for 5 Seconds...')
    s.write(b'F\\n')
    s.flush()
    time.sleep(5.0)
    print('>>> [STOPPING MOTORS]...')
    s.write(b'S\\n')
    s.flush()
    s.close()
    print('>>> [TEST COMPLETE]!')
except Exception as err:
    print('Serial Error:', err)
"""
    # Stop background service temporarily so port /dev/ttyACM0 is 100% exclusive
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl stop soccer_motor.service")
    time.sleep(1.0)

    print("\n[2] Sending 5-Second FORWARD Command to Wheels...")
    stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{pi_code}\"")
    output = stdout.read().decode().strip()
    print(output)

    # Re-enable service
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl start soccer_motor.service")
    ssh.close()

    print("\n" + "=" * 60)
    print("Watch the robot wheels. If no spin, check 12V battery switch!")
    print("=" * 60)

if __name__ == '__main__':
    main()
