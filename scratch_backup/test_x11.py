import subprocess

cmd = [
    "wsl", "-d", "Ubuntu", "--", "bash", "-c",
    "export DISPLAY=$(ip route show default | awk '{print $3}'):0; python3 -c \"import tkinter; root = tkinter.Tk(); root.title('X11 Test'); print('Tkinter Window Opened Successfully!')\""
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
