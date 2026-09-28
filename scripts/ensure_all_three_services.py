import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("   CHECKING & VERIFYING ALL 3 HARDWARE SERVICES ON PI")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)

    # 1. Restart services and docker
    print("[1] Starting Docker & Services on Pi...")
    ssh.exec_command("docker start soccer_bot_edge")
    time.sleep(2.0)
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl restart soccer_lidar.service soccer_camera.service soccer_motor.service")
    time.sleep(3.0)

    # 2. Check service status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active soccer_lidar.service soccer_camera.service soccer_motor.service")
    print("Systemd Service States:\n" + stdout.read().decode().strip())

    ssh.close()

    # 3. Test All 3 Ports from Laptop
    print("\n[2] Testing All 3 Socket Ports from Laptop:")
    # 5000: LIDAR
    try:
        s = socket.socket()
        s.settimeout(2.5)
        s.connect((PI_IP, 5000))
        data = s.recv(1024)
        print(f"  [LIDAR 5000]  -> ONLINE! ({len(data)} bytes of laser scan points)")
        s.close()
    except Exception as e:
        print(f"  [LIDAR 5000]  -> ERROR: {e}")

    # 8000: CAMERA
    try:
        s = socket.socket()
        s.settimeout(2.5)
        s.connect((PI_IP, 8000))
        data = s.recv(1024)
        print(f"  [CAMERA 8000] -> ONLINE! ({len(data)} bytes of live JPEG video)")
        s.close()
    except Exception as e:
        print(f"  [CAMERA 8000] -> ERROR: {e}")

    # 9000: MOTORS
    try:
        s = socket.socket()
        s.settimeout(2.5)
        s.connect((PI_IP, 9000))
        s.sendall(b'S')
        print(f"  [MOTORS 9000] -> ONLINE! (Ready for driving commands)")
        s.close()
    except Exception as e:
        print(f"  [MOTORS 9000] -> ERROR: {e}")

    print("=" * 60)

if __name__ == '__main__':
    main()
