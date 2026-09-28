import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("      CHECKING ARDUINO UNO & STARTING MOTOR CONTROLLER")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
    print("[1] SSH Connected to Raspberry Pi!")

    # Check Serial Ports
    print("\n[2] Checking Serial Hardware on Pi:")
    stdin, stdout, stderr = ssh.exec_command("ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null")
    ports_out = stdout.read().decode().strip()
    print(ports_out if ports_out else "No serial ports found")

    # Restart motor service
    print("\n[3] Restarting soccer_motor.service...")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl restart soccer_motor.service")
    time.sleep(3.0)

    # Check status & journalctl
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active soccer_motor.service ; journalctl -u soccer_motor.service -n 10 --no-pager")
    print("Service Status & Log:\n" + stdout.read().decode().strip())

    ssh.close()

    # Test Socket on Port 9000 from Laptop
    print("\n[4] Testing Socket Stream on Port 9000 from Laptop:")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.settimeout(2.5)
        s.connect((PI_IP, 9000))
        s.sendall(b'S')
        s.close()
        print("  [SUCCESS] Port 9000 is ONLINE & responsive!")
    except Exception as e:
        print(f"  [ERROR] {e}")

    print("=" * 60)

if __name__ == '__main__':
    main()
