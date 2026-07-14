import os
import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    try:
        print("Syncing fixed Jazzy C++ driver to Pi...")
        os.system(f'sshpass -p "{password}" rsync -avz --exclude="build" --exclude="install" --exclude="log" /home/sharmin/Desktop/iot/soccer_bot/src/ydlidar_ros2_driver {user}@{ip}:~/soccer_bot/src/')
        os.system(f'sshpass -p "{password}" rsync -avz --exclude="build" --exclude="install" --exclude="log" /home/sharmin/Desktop/iot/soccer_bot/src/YDLidar-SDK {user}@{ip}:~/soccer_bot/src/')
        
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {user}@{ip}', timeout=30)
        i = child.expect(['[Pp]assword:', pexpect.EOF, 'Are you sure'])
        if i == 2:
            child.sendline('yes')
            child.expect('[Pp]assword:')
            child.sendline(password)
        elif i == 0:
            child.sendline(password)
        child.expect(r'\$')
        
        print("Enabling Swap to prevent OOM...")
        child.sendline(f'echo "{password}" | sudo -S fallocate -l 2G /swapfile')
        child.expect(r'\$')
        child.sendline(f'echo "{password}" | sudo -S chmod 600 /swapfile')
        child.expect(r'\$')
        child.sendline(f'echo "{password}" | sudo -S mkswap /swapfile')
        child.expect(r'\$')
        child.sendline(f'echo "{password}" | sudo -S swapon /swapfile')
        child.expect(r'\$')
        
        # Kill the previous Python streams to free the port/camera
        child.sendline('killall python3 socat')
        child.expect(r'\$')
        
        print("Compiling C++ Driver on Pi (this will take 5-10 minutes)...")
        # Run it in a nohup so it doesn't get killed
        child.sendline('cd ~/soccer_bot && nohup bash -c "source /opt/ros/jazzy/setup.bash && colcon build --packages-select ydlidar_ros2_driver" > build_lidar.log 2>&1 &')
        child.expect(r'\$')
        
        print("Compilation started in background on Pi. You can check build_lidar.log")
        child.sendline('exit')
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
