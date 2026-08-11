import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("     DIAGNOSING & STARTING SENSOR STREAMS ON PI")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
        print("[1] Connected to Raspberry Pi via SSH!")
    except Exception as e:
        print(f"[FAIL] Could not connect to Pi: {e}")
        return

    # 1. Start Docker container for Lidar
    print("[2] Starting Docker container soccer_bot_edge...")
    ssh.exec_command("docker start soccer_bot_edge")
    time.sleep(2.0)

    # 2. Restart services
    print("[3] Restarting soccer_lidar and soccer_camera services...")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl restart soccer_lidar.service soccer_camera.service")
    time.sleep(3.0)

    # 3. Read journal logs
    print("\n--- SYSTEMD JOURNAL (LIDAR & CAMERA) ---")
    stdin, stdout, stderr = ssh.exec_command("journalctl -u soccer_lidar -u soccer_camera -n 15 --no-pager")
    print(stdout.read().decode().strip())

    ssh.close()

    # 4. Socket Tests from Laptop
    print("\n[4] Testing Socket Connections from Laptop:")
    # Lidar (5000)
    try:
        s = socket.socket()
        s.settimeout(2.5)
        s.connect((PI_IP, 5000))
        data = s.recv(1024)
        print(f"  [LIDAR 5000]  -> ONLINE! ({len(data)} bytes received)")
        s.close()
    except Exception as e:
        print(f"  [LIDAR 5000]  -> FAILED ({e})")

    # Camera (8000)
    try:
        s = socket.socket()
        s.settimeout(2.5)
        s.connect((PI_IP, 8000))
        data = s.recv(1024)
        print(f"  [CAMERA 8000] -> ONLINE! ({len(data)} bytes received)")
        s.close()
    except Exception as e:
        print(f"  [CAMERA 8000] -> FAILED ({e})")

    print("=" * 60)

if __name__ == '__main__':
    main()
