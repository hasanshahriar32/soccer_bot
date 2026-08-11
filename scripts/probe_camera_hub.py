import socket
import paramiko
import time

def main():
    print("1. Checking Pi Camera processes...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "python3|rpicam"')
    print(stdout.read().decode())
    
    print("2. Restarting Fast Camera Server on Pi...")
    ssh.exec_command('pkill -f fast_camera_server; pkill -f rpicam-vid; pkill -f picam_server; fuser -k 8000/tcp; sleep 1; nohup python3 /home/hasan/fast_camera_server.py > /tmp/camera_server.log 2>&1 &')
    time.sleep(2)
    
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/camera_server.log')
    print("--- Camera Server Log ---")
    print(stdout.read().decode())
    ssh.close()
    
    print("3. Testing TCP Stream from Laptop...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.0)
        s.connect(('192.168.0.135', 8000))
        data = s.recv(4096)
        print(f"[SUCCESS] Connected to Pi Camera server! Received {len(data)} bytes of JPEG data.")
        s.close()
    except Exception as e:
        print("[FAIL] Could not connect to Pi Camera server:", str(e))

if __name__ == '__main__':
    main()
