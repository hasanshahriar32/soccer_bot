import subprocess
import time

print("Reopening RViz GUI...")
cmd = [
    "wsl", "-d", "Ubuntu", "--", "bash", "-c",
    "export DISPLAY=$(ip route show default | awk '{print $3}'):0; export QT_QPA_PLATFORM=xcb; export LIBGL_ALWAYS_SOFTWARE=1; source /opt/ros/jazzy/setup.bash; rviz2 -d /mnt/c/Users/taufi/Desktop/soccer_bot/soccer_bot.rviz"
]

proc = subprocess.Popen(cmd)
time.sleep(2)
print("RViz GUI process launched successfully!")
