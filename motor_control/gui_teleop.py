import tkinter as tk
from tkinter import ttk
import socket
import threading
import time

PI_IP = '192.168.0.135'
MOTOR_PORT = 9000

class RobotTeleopGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚽ SOCCER BOT - WHEEL CONTROLLER")
        self.root.geometry("480x570")
        self.root.configure(bg="#121216")
        self.root.resizable(False, False)
        
        self.sock = None
        self.connect_socket()

        # Title Banner
        title_lbl = tk.Label(root, text="SOCCER BOT WHEEL CONTROLLER", font=("Segoe UI", 16, "bold"), fg="#00e5ff", bg="#121216")
        title_lbl.pack(pady=8)

        # Status Label
        self.status_lbl = tk.Label(root, text="● SERVER: 192.168.0.135:9000 (CONNECTED)", font=("Segoe UI", 10, "bold"), fg="#00e676", bg="#121216")
        self.status_lbl.pack(pady=2)

        # Mode Indicator
        self.mode_lbl = tk.Label(root, text="Current Action: STOPPED", font=("Segoe UI", 12, "bold"), fg="#ff5252", bg="#121216")
        self.mode_lbl.pack(pady=3)

        # Speed Control Section
        speed_frame = tk.Frame(root, bg="#1a1a24", bd=1, relief="solid")
        speed_frame.pack(fill="x", padx=30, pady=8)

        tk.Label(speed_frame, text="⚡ MOTOR SPEED / TORQUE LEVEL", font=("Segoe UI", 10, "bold"), fg="#ffd600", bg="#1a1a24").pack(anchor="w", padx=10, pady=2)
        
        slider_box = tk.Frame(speed_frame, bg="#1a1a24")
        slider_box.pack(fill="x", padx=10, pady=4)

        self.speed_val = tk.IntVar(value=220)
        self.speed_slider = tk.Scale(slider_box, from_=160, to=255, orient="horizontal", variable=self.speed_val,
                                     bg="#1a1a24", fg="#00e5ff", highlightthickness=0, font=("Segoe UI", 9, "bold"),
                                     troughcolor="#2a2a38", activebackground="#00e5ff")
        self.speed_slider.pack(fill="x", expand=True)

        # Control Frame
        btn_frame = tk.Frame(root, bg="#121216")
        btn_frame.pack(pady=6)

        btn_style = {"font": ("Segoe UI", 13, "bold"), "width": 10, "height": 2, "relief": "flat", "cursor": "hand2"}

        # UP (Forward)
        self.btn_fwd = tk.Button(btn_frame, text="▲\nFORWARD (W)", bg="#2e7d32", fg="white", activebackground="#43a047",
                                 command=lambda: self.drive_action('F'), **btn_style)
        self.btn_fwd.grid(row=0, column=1, padx=6, pady=6)

        # LEFT
        self.btn_left = tk.Button(btn_frame, text="◀\nSPIN LEFT (A)", bg="#1565c0", fg="white", activebackground="#1e88e5",
                                  command=lambda: self.drive_action('L'), **btn_style)
        self.btn_left.grid(row=1, column=0, padx=6, pady=6)

        # STOP (Space)
        self.btn_stop = tk.Button(btn_frame, text="⏹\nSTOP", bg="#c62828", fg="white", activebackground="#e53935",
                                  command=lambda: self.drive_action('S'), **btn_style)
        self.btn_stop.grid(row=1, column=1, padx=6, pady=6)

        # RIGHT
        self.btn_right = tk.Button(btn_frame, text="▶\nSPIN RIGHT (D)", bg="#1565c0", fg="white", activebackground="#1e88e5",
                                   command=lambda: self.drive_action('R'), **btn_style)
        self.btn_right.grid(row=1, column=2, padx=6, pady=6)

        # DOWN (Backward)
        self.btn_bwd = tk.Button(btn_frame, text="▼\nBACK (S)", bg="#d84315", fg="white", activebackground="#f4511e",
                                 command=lambda: self.drive_action('B'), **btn_style)
        self.btn_bwd.grid(row=2, column=1, padx=6, pady=6)

        # Instructions Footer
        footer = tk.Label(root, text="Keyboard: [W] Forward | [S] Back | [A] Spin Left | [D] Spin Right | [Space] STOP",
                          font=("Segoe UI", 9), fg="#757575", bg="#121216", justify="center")
        footer.pack(pady=6)

        # Key Bindings
        self.root.bind('<KeyPress-w>', lambda e: self.drive_action('F'))
        self.root.bind('<KeyPress-W>', lambda e: self.drive_action('F'))
        self.root.bind('<KeyPress-Up>', lambda e: self.drive_action('F'))

        self.root.bind('<KeyPress-s>', lambda e: self.drive_action('B'))
        self.root.bind('<KeyPress-S>', lambda e: self.drive_action('B'))
        self.root.bind('<KeyPress-Down>', lambda e: self.drive_action('B'))

        self.root.bind('<KeyPress-a>', lambda e: self.drive_action('L'))
        self.root.bind('<KeyPress-A>', lambda e: self.drive_action('L'))
        self.root.bind('<KeyPress-Left>', lambda e: self.drive_action('L'))

        self.root.bind('<KeyPress-d>', lambda e: self.drive_action('R'))
        self.root.bind('<KeyPress-D>', lambda e: self.drive_action('R'))
        self.root.bind('<KeyPress-Right>', lambda e: self.drive_action('R'))

        self.root.bind('<space>', lambda e: self.drive_action('S'))
        self.root.bind('<KeyPress-x>', lambda e: self.drive_action('S'))
        self.root.bind('<KeyPress-X>', lambda e: self.drive_action('S'))

    def connect_socket(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(2.0)
            self.sock.connect((PI_IP, MOTOR_PORT))
        except Exception as e:
            self.sock = None

    def drive_action(self, action):
        spd = self.speed_val.get()
        turn_spd = max(180, int(spd * 0.88)) # Strong starting torque for turns
        
        if action == 'F':
            pkt = f"L:{spd} R:{spd}\n"
            desc = f"FORWARD (Speed: {spd})"
            color = "#00e5ff"
        elif action == 'B':
            pkt = f"L:{-spd} R:{-spd}\n"
            desc = f"BACKWARD (Speed: {spd})"
            color = "#00e5ff"
        elif action == 'L':
            pkt = f"L:{-turn_spd} R:{turn_spd}\n"
            desc = f"SPIN LEFT (Turn Speed: {turn_spd})"
            color = "#00e5ff"
        elif action == 'R':
            pkt = f"L:{turn_spd} R:{-turn_spd}\n"
            desc = f"SPIN RIGHT (Turn Speed: {turn_spd})"
            color = "#00e5ff"
        else:
            pkt = "L:0 R:0\n"
            desc = "STOPPED"
            color = "#ff5252"

        self.mode_lbl.config(text=f"Action: {desc}", fg=color)

        def _worker():
            try:
                if self.sock is None:
                    self.connect_socket()
                if self.sock:
                    self.sock.sendall(pkt.encode('utf-8'))
            except Exception as e:
                self.connect_socket()
                if self.sock:
                    try:
                        self.sock.sendall(pkt.encode('utf-8'))
                    except:
                        pass

        threading.Thread(target=_worker, daemon=True).start()

    def on_closing(self):
        try:
            if self.sock:
                self.sock.sendall(b"L:0 R:0\n")
                time.sleep(0.1)
                self.sock.close()
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
