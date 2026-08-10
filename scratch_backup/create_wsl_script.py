import subprocess

script_content = """#!/bin/bash
source /opt/ros/jazzy/setup.bash
rviz2 "$@"
"""

cmd = ["wsl", "-d", "Ubuntu", "--", "bash", "-c", "cat << 'EOF' > ~/launch_rviz.sh\n" + script_content + "\nEOF\nchmod +x ~/launch_rviz.sh"]
subprocess.run(cmd)
print("Created launch_rviz.sh successfully!")
