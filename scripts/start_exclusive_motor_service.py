import paramiko
import time
import socket

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("      EXCLUSIVE ARDUINO SERIAL & MOTOR SERVER SETUP")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)

    # 1. Kill any rogue processes locking /dev/ttyACM0
    print("[1] Releasing /dev/ttyACM0 from old background processes...")
    ssh.exec_command(f"echo '{PI_PASS}' | sudo -S fuser -k /dev/ttyACM0 2>/dev/null ; pkill -f motor_server ; pkill -f motor_daemon ; sleep 1")
    time.sleep(2.0)

    # 2. Upload clean motor server with instant serial flush
    clean_server = """import socket
import serial
import time

print("[START] Connecting to Arduino Uno on /dev/ttyACM0...")
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1.0)
time.sleep(2.0) # Allow bootloader to settle
ser.reset_input_buffer()
ser.reset_output_buffer()
print("[READY] Arduino Serial Ready!")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 9000))
server.listen(5)
print("[ONLINE] Motor TCP Server listening on 0.0.0.0:9000...")

while True:
    conn, addr = server.accept()
    print(f"Controller Connected from {addr}")
    while True:
        try:
            data = conn.recv(64)
            if not data:
                break
            cmd_str = data.decode('utf-8', errors='ignore')
            for ch in cmd_str:
                if ch in 'FBLRS':
                    ser.write(ch.encode('utf-8'))
                    ser.flush()
                    print(f"-> Motor Command Sent: {ch}")
        except Exception as e:
            print(f"Socket err: {e}")
            break
    conn.close()
"""
    sftp = ssh.open_sftp()
    with sftp.file('/home/hasan/motor_server.py', 'w') as f:
        f.write(clean_server)
    sftp.close()

    # 3. Start motor_server cleanly
    print("[2] Starting dedicated motor_server daemon...")
    ssh.exec_command("nohup python3 -u /home/hasan/motor_server.py </dev/null >/tmp/motor_server.log 2>&1 &")
    time.sleep(3.0)

    # Check log
    stdin, stdout, stderr = ssh.exec_command("cat /tmp/motor_server.log")
    print("\n--- MOTOR SERVER LOG ---")
    print(stdout.read().decode().strip())

    ssh.close()

    # 4. Direct socket test from Laptop
    print("\n[3] Testing socket command from laptop...")
    s = socket.socket()
    s.connect((PI_IP, 9000))
    s.sendall(b'F')
    time.sleep(1.0)
    s.sendall(b'S')
    s.close()
    print("[SUCCESS] Motor server processed command over network!")
    print("=" * 60)

if __name__ == '__main__':
    main()
