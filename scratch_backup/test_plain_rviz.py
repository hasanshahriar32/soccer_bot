import subprocess

cmd = [
    "wsl", "-d", "Ubuntu", "--", "bash", "-c",
    "export DISPLAY=$(ip route show default | awk '{print $3}'):0; export QT_QPA_PLATFORM=xcb; export LIBGL_ALWAYS_SOFTWARE=1; source /opt/ros/jazzy/setup.bash; rviz2"
]

res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
