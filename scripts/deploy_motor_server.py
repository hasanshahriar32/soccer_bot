import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("   DEPLOYING PERMANENT MOTOR TCP SERVER ON RASPBERRY PI")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)

    # 1. Upload motor server
    print("[1] Uploading motor_server.py to Pi...")
    sftp = ssh.open_sftp()
    sftp.put('motor_control/motor_server.py', '/home/hasan/motor_server.py')
    sftp.close()

    # 2. Kill old and start new motor server
    print("[2] Starting motor_server on Port 9000...")
    ssh.exec_command("pkill -f motor_server ; fuser -k 9000/tcp ; sleep 1 ; nohup python3 -u /home/hasan/motor_server.py </dev/null >/tmp/motor_server.log 2>&1 &")
    time.sleep(2.5)

    # 3. Create permanent systemd service
    service_def = """[Unit]
Description=Soccer Bot Motor TCP Controller (Port 9000)
After=network.target

[Service]
Type=simple
User=hasan
ExecStart=/usr/bin/python3 -u /home/hasan/motor_server.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/soccer_motor.service', 'w') as f:
        f.write(service_def)
    sftp.close()

    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S cp /tmp/soccer_motor.service /etc/systemd/system/")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl daemon-reload")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl enable soccer_motor.service")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S systemctl restart soccer_motor.service")
    time.sleep(2.0)

    # Check status
    stdin, stdout, stderr = ssh.exec_command("systemctl is-active soccer_motor.service ; cat /tmp/motor_server.log")
    print("Service Status & Log:\n" + stdout.read().decode().strip())

    ssh.close()

    # 4. Test Socket Connection from Laptop
    print("\n[3] Testing Socket on Port 9000 from Laptop...")
    try:
        s = socket.socket()
        s.settimeout(3.0)
        s.connect((PI_IP, 9000))
        s.sendall(b'S')
        s.close()
        print("[SUCCESS] Motor TCP Server is ONLINE on Port 9000 & responsive!")
    except Exception as e:
        print(f"[FAIL] Socket test error: {e}")

    print("=" * 60)

if __name__ == '__main__':
    main()
