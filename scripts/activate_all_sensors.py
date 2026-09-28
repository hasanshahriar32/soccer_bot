import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("     ACTIVATING & VERIFYING ALL SENSOR STREAMS ON PI")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
    print("[1] SSH Connected to Raspberry Pi (192.168.0.135)!")

    # Start Docker for Lidar
    print("[2] Starting Docker container soccer_bot_edge...")
    ssh.exec_command("docker start soccer_bot_edge")
    time.sleep(2.0)

    # Restart Lidar and Camera systemd services
    print("[3] Restarting soccer_lidar and soccer_camera services...")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl restart soccer_lidar.service soccer_camera.service soccer_motor.service")
    time.sleep(4.0)

    # Check process states
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active soccer_lidar.service soccer_camera.service soccer_motor.service ; netstat -tlpn 2>/dev/null | grep -E '5000|8000|9000'")
    print("\n--- ACTIVE SERVICES & PORTS ON PI ---")
    print(stdout.read().decode().strip())

    ssh.close()

    # Test all 3 socket streams from Laptop
    print("\n[4] Testing Live Data Streams from Laptop:")
    time.sleep(1.0)

    # Lidar (5000)
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 5000))
        data = s.recv(1024)
        print(f"  [LIDAR 5000]  -> SUCCESS! Received {len(data)} bytes of laser scan points.")
        s.close()
    except Exception as e:
        print(f"  [LIDAR 5000]  -> Error: {e}")

    # Camera (8000)
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 8000))
        data = s.recv(1024)
        print(f"  [CAMERA 8000] -> SUCCESS! Received {len(data)} bytes of live JPEG video frames.")
        s.close()
    except Exception as e:
        print(f"  [CAMERA 8000] -> Error: {e}")

    # Motors (9000)
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 9000))
        s.sendall(b'S')
        print(f"  [MOTORS 9000] -> SUCCESS! Motor controller is ONLINE and ready.")
        s.close()
    except Exception as e:
        print(f"  [MOTORS 9000] -> Error: {e}")

    print("=" * 60)

if __name__ == '__main__':
    main()
