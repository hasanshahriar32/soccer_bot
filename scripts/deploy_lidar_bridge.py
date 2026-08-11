import paramiko
import time

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print(f"Connecting to Raspberry Pi ({ip})...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username=user, password=password, timeout=10)
    print("Connected! Starting Docker container if not running...")
    
    ssh.exec_command('docker start soccer_bot_edge')
    time.sleep(2)
    
    print("Uploading bridge_scan_to_laptop.py...")
    with open('scripts/bridge_scan_to_laptop.py', 'r') as f:
        code = f.read()
        
    sftp = ssh.open_sftp()
    with sftp.file('/home/hasan/bridge_scan_to_laptop.py', 'w') as remote_file:
        remote_file.write(code)
    sftp.close()
    
    print("Freeing port 5000 on Pi host...")
    ssh.exec_command('pkill -f python_socat; fuser -k 5000/tcp')
    time.sleep(1)
    
    print("Copying bridge script into Docker container...")
    ssh.exec_command('docker cp /home/hasan/bridge_scan_to_laptop.py soccer_bot_edge:/bridge_scan_to_laptop.py')
    ssh.exec_command('docker exec soccer_bot_edge pkill -f bridge_scan_to_laptop')
    time.sleep(1)
    
    print("Starting Lidar TCP Bridge Node inside Docker...")
    ssh.exec_command('docker exec -d soccer_bot_edge /bin/bash -c "source /opt/ros/jazzy/setup.bash && python3 -u /bridge_scan_to_laptop.py > /tmp/lidar_bridge.log 2>&1"')
    
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command('docker exec soccer_bot_edge cat /tmp/lidar_bridge.log')
    print("--- Lidar Bridge Log ---")
    print(stdout.read().decode())
    
    ssh.close()
    print("[SUCCESS] Lidar scan streaming is now ACTIVE on port 5000!")

if __name__ == '__main__':
    main()
