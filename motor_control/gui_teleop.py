import tkinter as tk
import socket
import threading
import time

PI_IP = '192.168.0.135'
MOTOR_PORT = 9000

class RobotTeleopGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚽ SOCCER BOT - WHEEL CONTROLLER")
        self.root.geometry("460x520")
        self.root.configure(bg="#121216")
        self.root.resizable(False, False)

        # Title Banner
        title_lbl = tk.Label(root, text="SOCCER BOT WHEEL CONTROLLER", font=("Segoe UI", 16, "bold"), fg="#00e5ff", bg="#121216")
        title_lbl.pack(pady=10)

        # Status Label
        self.status_lbl = tk.Label(root, text="● SERVER: 192.168.0.135:9000 (READY)", font=("Segoe UI", 10, "bold"), fg="#00e676", bg="#121216")
        self.status_lbl.pack(pady=3)

        # Mode Indicator
        self.mode_lbl = tk.Label(root, text="Current Action: STOPPED", font=("Segoe UI", 12, "bold"), fg="#ff5252", bg="#121216")
        self.mode_lbl.pack(pady=4)

        # Control Frame
        btn_frame = tk.Frame(root, bg="#121216")
        btn_frame.pack(pady=10)

        btn_style = {"font": ("Segoe UI", 13, "bold"), "width": 10, "height": 2, "relief": "flat", "cursor": "hand2"}

        # UP (Forward)
        self.btn_fwd = tk.Button(btn_frame, text="▲\nFORWARD (W)", bg="#2e7d32", fg="white", activebackground="#43a047",
                                 command=lambda: self.send_cmd('F'), **btn_style)
        self.btn_fwd.grid(row=0, column=1, padx=6, pady=6)

        # LEFT
        self.btn_left = tk.Button(btn_frame, text="◀\nLEFT (A)", bg="#1565c0", fg="white", activebackground="#1e88e5",
                                  command=lambda: self.send_cmd('L'), **btn_style)
        self.btn_left.grid(row=1, column=0, padx=6, pady=6)

        # STOP (Space)
        self.btn_stop = tk.Button(btn_frame, text="⏹\nSTOP", bg="#c62828", fg="white", activebackground="#e53935",
                                  command=lambda: self.send_cmd('S'), **btn_style)
        self.btn_stop.grid(row=1, column=1, padx=6, pady=6)

        # RIGHT
        self.btn_right = tk.Button(btn_frame, text="▶\nRIGHT (D)", bg="#1565c0", fg="white", activebackground="#1e88e5",
                                   command=lambda: self.send_cmd('R'), **btn_style)
        self.btn_right.grid(row=1, column=2, padx=6, pady=6)

        # DOWN (Backward)
        self.btn_bwd = tk.Button(btn_frame, text="▼\nBACK (S)", bg="#d84315", fg="white", activebackground="#f4511e",
                                 command=lambda: self.send_cmd('B'), **btn_style)
        self.btn_bwd.grid(row=2, column=1, padx=6, pady=6)

        # Instructions Footer
        footer = tk.Label(root, text="Keyboard Shortcuts:\n[ W / ↑ ] Forward | [ S / ↓ ] Backward\n[ A / ← ] Spin Left | [ D / → ] Spin Right\n[ Space / X ] STOP",
                          font=("Segoe UI", 9), fg="#757575", bg="#121216", justify="center")
        footer.pack(pady=8)

        # Key Bindings
        self.root.bind('<KeyPress-w>', lambda e: self.send_cmd('F'))
        self.root.bind('<KeyPress-W>', lambda e: self.send_cmd('F'))
        self.root.bind('<KeyPress-Up>', lambda e: self.send_cmd('F'))

        self.root.bind('<KeyPress-s>', lambda e: self.send_cmd('B'))
        self.root.bind('<KeyPress-S>', lambda e: self.send_cmd('B'))
        self.root.bind('<KeyPress-Down>', lambda e: self.send_cmd('B'))

        self.root.bind('<KeyPress-a>', lambda e: self.send_cmd('L'))
        self.root.bind('<KeyPress-A>', lambda e: self.send_cmd('L'))
        self.root.bind('<KeyPress-Left>', lambda e: self.send_cmd('L'))

        self.root.bind('<KeyPress-d>', lambda e: self.send_cmd('R'))
        self.root.bind('<KeyPress-D>', lambda e: self.send_cmd('R'))
        self.root.bind('<KeyPress-Right>', lambda e: self.send_cmd('R'))

        self.root.bind('<space>', lambda e: self.send_cmd('S'))
        self.root.bind('<KeyPress-x>', lambda e: self.send_cmd('S'))
        self.root.bind('<KeyPress-X>', lambda e: self.send_cmd('S'))

    def send_cmd(self, cmd):
        def _worker():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(1.5)
                s.connect((PI_IP, MOTOR_PORT))
                s.sendall(cmd.encode('utf-8'))
                s.close()
                action_names = {'F': 'FORWARD (Moving)', 'B': 'BACKWARD (Moving)', 'L': 'SPINNING LEFT', 'R': 'SPINNING RIGHT', 'S': 'STOPPED'}
                color = "#00e5ff" if cmd != 'S' else "#ff5252"
                self.mode_lbl.config(text=f"Action: {action_names.get(cmd, cmd)}", fg=color)
            except Exception as e:
                self.mode_lbl.config(text=f"Error sending: {e}", fg="#ff1744")

        threading.Thread(target=_worker, daemon=True).start()

    def on_closing(self):
        try:
            self.send_cmd('S')
            time.sleep(0.1)
        except:
            pass
        self.root.destroy()

def main():
    root = tk.Tk()
    app = RobotTeleopGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == '__main__':
    main()
