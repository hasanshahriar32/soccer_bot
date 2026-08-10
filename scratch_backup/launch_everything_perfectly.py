import subprocess
import time
import os

print("1. Restarting VcXsrv with -ac -multiwindow flags...")
subprocess.run("taskkill /f /im vcxsrv.exe", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
time.sleep(1)

vcxsrv_path = r"C:\Program Files\VcXsrv\vcxsrv.exe"
vcxsrv_cmd = f'"{vcxsrv_path}" :0 -ac -multiwindow -clipboard -wgl'
subprocess.Popen(vcxsrv_cmd, shell=True)
time.sleep(2)

print("2. Launching native ROS 2 RViz GUI...")
wsl_cmd = [
    "wsl", "-d", "Ubuntu", "--", "bash", "-c",
    "export DISPLAY=$(ip route show default | awk '{print $3}'):0; export LIBGL_ALWAYS_INDIRECT=1; source /opt/ros/jazzy/setup.bash; rviz2 -d /mnt/c/Users/taufi/Desktop/soccer_bot/soccer_bot.rviz"
]

subprocess.Popen(wsl_cmd)
print("3. Done! RViz window should be visible on your screen.")
