import paramiko
import time

def main():
    laptop_ip = '192.168.0.108'
    pi_ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print(f"Connecting to Raspberry Pi ({pi_ip})...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(pi_ip, username=user, password=password, timeout=10)
    print("[OK] Connected to Raspberry Pi!")
    
    # 1. Update camera stream destination
    camera_script = f"""#!/bin/bash
pkill -f rpicam-vid
pkill -f picam_server
sleep 1
nohup rpicam-vid -t 0 --inline -o tcp://{laptop_ip}:8000 --codec mjpeg --width 640 --height 480 --framerate 20 --nopreview > /tmp/camera.log 2>&1 &
echo "Camera stream initiated to {laptop_ip}:8000"
"""
    sftp = ssh.open_sftp()
    with sftp.file('/home/hasan/start_camera.sh', 'w') as f:
        f.write(camera_script)
    sftp.close()
    
    ssh.exec_command('chmod +x /home/hasan/start_camera.sh')
    print(f"[OK] Configured Pi camera stream to send to {laptop_ip}:8000")
    
    # 2. Start Camera stream
    ssh.exec_command('bash /home/hasan/start_camera.sh')
    print("[OK] Started Camera streaming daemon on Pi")
    
    ssh.close()
    print("\n[SUCCESS] Pi transmission is ACTIVE and streaming to laptop!")

if __name__ == '__main__':
    main()
