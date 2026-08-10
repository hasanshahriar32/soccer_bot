import subprocess
import time

print("1. Restarting VcXsrv X-Server...")
subprocess.run("taskkill /f /im vcxsrv.exe", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
time.sleep(1)

vcxsrv_path = r"C:\Program Files\VcXsrv\vcxsrv.exe"
vcxsrv_cmd = f'"{vcxsrv_path}" :0 -ac -multiwindow -clipboard -wgl'
subprocess.Popen(vcxsrv_cmd, shell=True)
time.sleep(2)

print("2. Starting Openbox Window Manager & RViz GUI in WSL...")
wsl_cmd = [
    "wsl", "-d", "Ubuntu", "--", "bash", "-c",
    "export DISPLAY=$(ip route show default | awk '{print $3}'):0; openbox --replace & sleep 1; export QT_QPA_PLATFORM=xcb; export LIBGL_ALWAYS_SOFTWARE=1; source /opt/ros/jazzy/setup.bash; rviz2 -d /mnt/c/Users/taufi/Desktop/soccer_bot/soccer_bot.rviz"
]

subprocess.Popen(wsl_cmd)
print("3. Done! Window Manager and RViz are running.")
