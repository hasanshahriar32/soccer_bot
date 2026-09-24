import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time
import serial
import serial.tools.list_ports

class UniversalRobotTeleopGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚽ SOCCER BOT - UNIVERSAL MOTOR CONTROLLER")
        self.root.geometry("520x680")
        self.root.configure(bg="#121216")
        self.root.resizable(False, False)
        
        self.sock = None
        self.ser = None
        self.connection_mode = "WIFI"  # "WIFI" or "USB"

        # Title Banner
        title_lbl = tk.Label(root, text="SOCCER BOT MOTOR CONTROLLER", font=("Segoe UI", 16, "bold"), fg="#00e5ff", bg="#121216")
        title_lbl.pack(pady=6)

        # Connection Mode Frame
        conn_frame = tk.LabelFrame(root, text=" 📡 Connection Setup ", font=("Segoe UI", 9, "bold"), fg="#ffd600", bg="#1a1a24", bd=1)
        conn_frame.pack(fill="x", padx=25, pady=4)

        # Wi-Fi Row
        wifi_row = tk.Frame(conn_frame, bg="#1a1a24")
        wifi_row.pack(fill="x", padx=8, pady=4)
        tk.Label(wifi_row, text="Robot IP:", font=("Segoe UI", 9, "bold"), fg="white", bg="#1a1a24").pack(side="left")
        self.ip_entry = tk.Entry(wifi_row, font=("Segoe UI", 10), width=16, bg="#2a2a38", fg="#00e5ff", insertbackground="white")
        self.ip_entry.insert(0, "10.127.69.146")
        self.ip_entry.pack(side="left", padx=6)
        
        self.btn_wifi_connect = tk.Button(wifi_row, text="Connect Wi-Fi", font=("Segoe UI", 9, "bold"), bg="#0288d1", fg="white",
                                          command=self.connect_wifi, relief="flat", cursor="hand2")
        self.btn_wifi_connect.pack(side="left", padx=4)

        # USB Serial Row
        usb_row = tk.Frame(conn_frame, bg="#1a1a24")
        usb_row.pack(fill="x", padx=8, pady=4)
        tk.Label(usb_row, text="USB Port:", font=("Segoe UI", 9, "bold"), fg="white", bg="#1a1a24").pack(side="left")
        
        self.port_combo = ttk.Combobox(usb_row, width=14, state="readonly")
        self.refresh_com_ports()
        self.port_combo.pack(side="left", padx=6)

        self.btn_refresh = tk.Button(usb_row, text="🔄", font=("Segoe UI", 9), bg="#37474f", fg="white",
                                     command=self.refresh_com_ports, relief="flat", cursor="hand2")
        self.btn_refresh.pack(side="left", padx=2)

        self.btn_usb_connect = tk.Button(usb_row, text="Connect USB", font=("Segoe UI", 9, "bold"), bg="#7b1fa2", fg="white",
                                         command=self.connect_usb, relief="flat", cursor="hand2")
        self.btn_usb_connect.pack(side="left", padx=4)

        # Status Label
        self.status_lbl = tk.Label(root, text="● STATUS: NOT CONNECTED", font=("Segoe UI", 10, "bold"), fg="#ff5252", bg="#121216")
        self.status_lbl.pack(pady=4)

        # Mode Indicator
        self.mode_lbl = tk.Label(root, text="Current Action: STOPPED", font=("Segoe UI", 12, "bold"), fg="#757575", bg="#121216")
        self.mode_lbl.pack(pady=2)

        # Speed Control Section
        speed_frame = tk.Frame(root, bg="#1a1a24", bd=1, relief="solid")
        speed_frame.pack(fill="x", padx=25, pady=6)

        header_box = tk.Frame(speed_frame, bg="#1a1a24")
        header_box.pack(fill="x", padx=10, pady=2)
        
        tk.Label(header_box, text="⚡ MOTOR SPEED (PWM)", font=("Segoe UI", 10, "bold"), fg="#ffd600", bg="#1a1a24").pack(side="left")
        self.speed_display = tk.Label(header_box, text="180 / 255 (Level 3)", font=("Segoe UI", 10, "bold"), fg="#00e5ff", bg="#1a1a24")
        self.speed_display.pack(side="right")
        
        slider_box = tk.Frame(speed_frame, bg="#1a1a24")
        slider_box.pack(fill="x", padx=10, pady=4)

        self.speed_val = tk.IntVar(value=180)
        self.speed_slider = tk.Scale(slider_box, from_=90, to=255, orient="horizontal", variable=self.speed_val,
                                     bg="#1a1a24", fg="#00e5ff", highlightthickness=0, font=("Segoe UI", 9, "bold"),
                                     troughcolor="#2a2a38", activebackground="#00e5ff", showvalue=False,
                                     command=self.update_slider_label)
        self.speed_slider.pack(fill="x", expand=True)

        # Speed Presets
        presets_box = tk.Frame(speed_frame, bg="#1a1a24")
        presets_box.pack(fill="x", padx=10, pady=4)
        
        tk.Button(presets_box, text="1: Slow (100)", bg="#37474f", fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self.set_preset(100), relief="flat", cursor="hand2").pack(side="left", padx=3, expand=True, fill="x")
        tk.Button(presets_box, text="2: Normal (135)", bg="#37474f", fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self.set_preset(135), relief="flat", cursor="hand2").pack(side="left", padx=3, expand=True, fill="x")
        tk.Button(presets_box, text="3: Medium (175)", bg="#37474f", fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self.set_preset(175), relief="flat", cursor="hand2").pack(side="left", padx=3, expand=True, fill="x")
        tk.Button(presets_box, text="4: Fast (215)", bg="#37474f", fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self.set_preset(215), relief="flat", cursor="hand2").pack(side="left", padx=3, expand=True, fill="x")
        tk.Button(presets_box, text="5: Max (255)", bg="#37474f", fg="white", font=("Segoe UI", 9, "bold"),
                  command=lambda: self.set_preset(255), relief="flat", cursor="hand2").pack(side="left", padx=3, expand=True, fill="x")

        # Control Buttons Frame
        btn_frame = tk.Frame(root, bg="#121216")
        btn_frame.pack(pady=6)

        btn_style = {"font": ("Segoe UI", 12, "bold"), "width": 11, "height": 2, "relief": "flat", "cursor": "hand2"}

        # UP (Forward)
        self.btn_fwd = tk.Button(btn_frame, text="▲\nFORWARD (W)", bg="#2e7d32", fg="white", activebackground="#43a047",
                                 command=lambda: self.drive_action('F'), **btn_style)
        self.btn_fwd.grid(row=0, column=1, padx=6, pady=4)

        # LEFT
        self.btn_left = tk.Button(btn_frame, text="◀\nSPIN LEFT (A)", bg="#1565c0", fg="white", activebackground="#1e88e5",
                                  command=lambda: self.drive_action('L'), **btn_style)
        self.btn_left.grid(row=1, column=0, padx=6, pady=4)

        # STOP (Space)
        self.btn_stop = tk.Button(btn_frame, text="⏹\nSTOP (Space)", bg="#c62828", fg="white", activebackground="#e53935",
                                  command=lambda: self.drive_action('S'), **btn_style)
        self.btn_stop.grid(row=1, column=1, padx=6, pady=4)

        # RIGHT
        self.btn_right = tk.Button(btn_frame, text="▶\nSPIN RIGHT (D)", bg="#1565c0", fg="white", activebackground="#1e88e5",
                                   command=lambda: self.drive_action('R'), **btn_style)
        self.btn_right.grid(row=1, column=2, padx=6, pady=4)

        # DOWN (Backward)
        self.btn_bwd = tk.Button(btn_frame, text="▼\nBACK (S)", bg="#d84315", fg="white", activebackground="#f4511e",
                                 command=lambda: self.drive_action('B'), **btn_style)
        self.btn_bwd.grid(row=2, column=1, padx=6, pady=4)

        # Instructions Footer
        footer = tk.Label(root, text="Keyboard: [W] Forward | [S] Back | [A] Left | [D] Right | [Space] STOP",
                          font=("Segoe UI", 9), fg="#757575", bg="#121216", justify="center")
        footer.pack(pady=4)

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

        # Auto-try Wi-Fi connect in background on startup
        threading.Thread(target=self.connect_wifi, daemon=True).start()

    def refresh_com_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)
        else:
            self.port_combo.set("No COM Ports")

    def connect_wifi(self):
        ip = self.ip_entry.get().strip()
        port = 9000
        try:
            self.status_lbl.config(text=f"● CONNECTING TO {ip}:{port}...", fg="#ffd600")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.settimeout(2.0)
            s.connect((ip, port))
            self.sock = s
            self.connection_mode = "WIFI"
            self.status_lbl.config(text=f"● WI-FI CONNECTED ({ip}:9000)", fg="#00e676")
        except Exception as e:
            self.sock = None
            self.status_lbl.config(text=f"● WI-FI FAILED ({ip}:9000)", fg="#ff5252")

    def connect_usb(self):
        port = self.port_combo.get().strip()
        if not port or "No COM" in port:
            messagebox.showwarning("No Port", "Please plug in Arduino Uno USB and click 🔄 to refresh!")
            return
        try:
            self.status_lbl.config(text=f"● OPENING {port} @ 9600 BAUD...", fg="#ffd600")
            s = serial.Serial(port, 9600, timeout=1.0)
            time.sleep(1.5)
            self.ser = s
            self.connection_mode = "USB"
            self.status_lbl.config(text=f"● USB CONNECTED ({port} @ 9600 Baud)", fg="#00e676")
        except Exception as e:
            self.ser = None
            self.status_lbl.config(text=f"● USB FAILED ({port}): {e}", fg="#ff5252")

    def update_slider_label(self, val):
        v = int(val)
        lvl = 1 if v < 115 else (2 if v < 155 else (3 if v < 195 else (4 if v < 235 else 5)))
        self.speed_display.config(text=f"{v} / 255 (Level {lvl})")

    def set_preset(self, val):
        self.speed_val.set(val)
        self.update_slider_label(val)

    def drive_action(self, action):
        spd = self.speed_val.get()
        lvl = '1' if spd < 115 else ('2' if spd < 155 else ('3' if spd < 195 else ('4' if spd < 235 else '5')))
        
        desc_map = {
            'F': ("FORWARD", "#00e5ff"),
            'B': ("BACKWARD", "#00e5ff"),
            'L': ("SPIN LEFT", "#00e5ff"),
            'R': ("SPIN RIGHT", "#00e5ff"),
            'S': ("STOPPED", "#ff5252")
        }
        name, col = desc_map.get(action, ("STOPPED", "#ff5252"))
        self.mode_lbl.config(text=f"Action: {name} (PWM: {spd})", fg=col)

        def _send():
            if self.connection_mode == "USB" and self.ser and self.ser.is_open:
                try:
                    if action != 'S':
                        self.ser.write(lvl.encode())
                        time.sleep(0.01)
                    self.ser.write(action.encode())
                    self.ser.flush()
                except Exception as err:
                    print(f"USB send err: {err}")
            elif self.connection_mode == "WIFI":
                turn_spd = max(90, int(spd * 0.85))
                if action == 'F':
                    pkt = f"SET:{spd},{spd}\n"
                elif action == 'B':
                    pkt = f"SET:{-spd},{-spd}\n"
                elif action == 'L':
                    pkt = f"SET:{-turn_spd},{turn_spd}\n"
                elif action == 'R':
                    pkt = f"SET:{turn_spd},{-turn_spd}\n"
                else:
                    pkt = "SET:0,0\n"

                try:
                    if self.sock:
                        self.sock.sendall(pkt.encode('utf-8'))
                except Exception:
                    self.connect_wifi()
                    if self.sock:
                        try:
                            self.sock.sendall(pkt.encode('utf-8'))
                        except:
                            pass

        threading.Thread(target=_send, daemon=True).start()

    def on_closing(self):
        try:
            if self.sock:
                self.sock.sendall(b"SET:0,0\n")
                self.sock.close()
            if self.ser and self.ser.is_open:
                self.ser.write(b'S')
                self.ser.close()
        except:
            pass
        self.root.destroy()

def main():
    root = tk.Tk()
    app = UniversalRobotTeleopGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == '__main__':
    main()
