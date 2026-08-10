import subprocess
import time

print("1. Launching RViz2...")
cmd = [
    "wsl", "-d", "Ubuntu", "--", "bash", "-c",
    "export DISPLAY=$(ip route show default | awk '{print $3}'):0; export QT_QPA_PLATFORM=xcb; export LIBGL_ALWAYS_SOFTWARE=1; source /opt/ros/jazzy/setup.bash; rviz2"
]
subprocess.Popen(cmd)

time.sleep(3)

print("2. Bringing RViz window to foreground...")
ps_script = """
$wshell = New-Object -ComObject wscript.shell
$wshell.AppActivate('rviz2')
$wshell.AppActivate('RViz')
"""
subprocess.run(["powershell", "-Command", ps_script])
print("Done!")
