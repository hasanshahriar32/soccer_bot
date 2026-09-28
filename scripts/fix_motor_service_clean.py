import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("      CLEANING & FIXING MOTOR SERVICE (PORT 9000)")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)

    # 1. Stop systemd service and kill all old processes on port 9000 & /dev/ttyACM0
    print("[1] Terminating old processes...")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl stop soccer_motor.service")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S fuser -k 9000/tcp ; echo '{PI_PASS}' | sudo -S fuser -k /dev/ttyACM0 ; pkill -9 -f motor_server ; sleep 1")
    time.sleep(2.0)

    # 2. Write clean motor server script directly
    clean_server_code = """import socket
import serial
import time
import sys

print("[1] Opening /dev/ttyACM0 @ 9600 baud...", flush=True)
try:
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0.1)
    time.sleep(2.0)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print("[2] Serial port open and ready!", flush=True)
except Exception as e:
    print(f"[ERROR] Serial error: {e}", flush=True)
    sys.exit(1)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
server.bind(('0.0.0.0', 9000))
server.listen(5)
print("[3] Motor Server listening on 0.0.0.0:9000...", flush=True)

while True:
    try:
        conn, addr = server.accept()
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print(f"[CLIENT] Connected from {addr}", flush=True)
        while True:
            data = conn.recv(64)
            if not data:
                break
            text = data.decode('utf-8', errors='ignore')
            for ch in text:
                if ch in 'FBLRS':
                    ser.write(ch.encode('utf-8'))
                    ser.flush()
                    print(f"[EXEC] Motor Command -> '{ch}'", flush=True)
        conn.close()
        print("[CLIENT] Disconnected", flush=True)
    except Exception as err:
        print(f"[ERR] {err}", flush=True)
        time.sleep(0.5)
"""
    sftp = ssh.open_sftp()
    with sftp.file('/home/hasan/motor_server.py', 'w') as f:
        f.write(clean_server_code)
    sftp.close()

    # 3. Start via systemd
    print("[2] Starting clean systemd soccer_motor.service...")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl start soccer_motor.service")
    time.sleep(3.0)

    # 4. Check status & journalctl
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active soccer_motor.service ; journalctl -u soccer_motor.service -n 10 --no-pager")
    print("\n--- SERVICE STATUS & LOG ---")
    print(stdout.read().decode().strip())

    ssh.close()

    # 5. Socket test with live command
    print("\n[3] Testing socket command 'F' then 'S' from laptop...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.connect((PI_IP, 9000))
    s.sendall(b'F')
    time.sleep(1.0)
    s.sendall(b'S')
    s.close()
    print("[SUCCESS] Test command sent and verified!")
    print("=" * 60)

if __name__ == '__main__':
    main()
