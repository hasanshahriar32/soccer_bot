import paramiko
import time
import subprocess
import os

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("==========================================")
    print("    STARTING SOCCER BOT ROBOTICS SYSTEM   ")
    print("==========================================")

    # 1. Start Raspberry Pi Sensors over SSH
    print("\n[1/3] Connecting to Raspberry Pi & starting Lidar + Camera...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=10)
        
        # Kill previous sensor instances if running
        ssh.exec_command("sudo killall -9 rpicam-vid python3 start_camera.sh ; docker stop soccer_bot_edge")
        time.sleep(1)
        
        # Launch Lidar (5000) and Camera (8080)
        ssh.exec_command("nohup python3 ~/python_socat.py > ~/socat.log 2>&1 &")
        ssh.exec_command("nohup python3 ~/picam_server.py > ~/camera.log 2>&1 &")
        time.sleep(2)
        
        s, o, e = ssh.exec_command("ps aux | grep -E 'python_socat|picam_server'")
        print("Pi Sensors Active Status:\n", o.read().decode())
        ssh.close()
    except Exception as err:
        print("Warning/Error connecting to Pi:", err)

    # 2. Check / Start VcXsrv X-Server on Windows
    print("\n[2/3] Checking VcXsrv X-Server on Windows...")
    tasklist = subprocess.check_output("tasklist", shell=True).decode()
    if "vcxsrv.exe" not in tasklist.lower():
        print("Starting VcXsrv X-Server...")
        vcxsrv_path = r"C:\Program Files\VcXsrv\vcxsrv.exe"
        if not os.path.exists(vcxsrv_path):
            vcxsrv_path = r"C:\Program Files (x86)\VcXsrv\vcxsrv.exe"
        
        if os.path.exists(vcxsrv_path):
            subprocess.Popen([vcxsrv_path, ":0", "-ac", "-multiwindow", "-clipboard", "-wgl"])
            time.sleep(2)
        else:
            print("VcXsrv path not found, relying on default DISPLAY...")

    # 3. Launch ROS 2 Hub Nodes & RViz inside WSL
    print("\n[3/3] Launching ROS 2 Sensor Hubs & RViz2 GUI inside WSL...")
    
    # Launch Openbox Window Manager in WSL if needed
    subprocess.Popen('wsl -d Ubuntu -- bash -c "export DISPLAY=$(ip route show default | awk \'{print $3}\'):0 && openbox &"', shell=True)
    time.sleep(1)
    
    # Launch Lidar Hub Node
    subprocess.Popen('wsl -d Ubuntu -- bash -c "source /opt/ros/jazzy/setup.bash && python3 /mnt/c/Users/taufi/Desktop/soccer_bot/raw_lidar_publisher.py"', shell=True)
    
    # Launch Camera Hub Node
    subprocess.Popen('wsl -d Ubuntu -- bash -c "source /opt/ros/jazzy/setup.bash && python3 /mnt/c/Users/taufi/Desktop/soccer_bot/src/soccer_vision/soccer_vision/camera_hub_node.py"', shell=True)
    
    # Launch 3D Robot Model Publisher Node
    subprocess.Popen('wsl -d Ubuntu -- bash -c "source /opt/ros/jazzy/setup.bash && python3 /mnt/c/Users/taufi/Desktop/soccer_bot/robot_model_publisher.py"', shell=True)
    
    time.sleep(2)
    
    # Launch RViz GUI
    print("Opening RViz GUI...")
    rviz_cmd = (
        'wsl -d Ubuntu -- bash -c "'
        'export DISPLAY=$(ip route show default | awk \'{print $3}\'):0 && '
        'export QT_QPA_PLATFORM=xcb && '
        'export LIBGL_ALWAYS_SOFTWARE=1 && '
        'source /opt/ros/jazzy/setup.bash && '
        'rviz2 -d /mnt/c/Users/taufi/Desktop/soccer_bot/soccer_bot.rviz"'
    )
    subprocess.Popen(rviz_cmd, shell=True)

    print("\n==========================================")
    print(" SUCCESS! System launched.")
    print(" Camera Web Stream: http://192.168.0.135:8080/video")
    print("==========================================")

if __name__ == '__main__':
    main()
