#!/usr/bin/env python3
"""
====================================================================
  SOCCER BOT - UNIVERSAL MOTOR CONTROLLER & AUTONOMOUS BALL FOLLOWER
====================================================================
Features:
    1. Dual Mode: Wi-Fi TCP Socket (Port 9000) or Direct USB Serial.
    2. Precision PWM Speed slider & 5-level presets.
    3. Manual directional controls (W, A, S, D, Space).
    4. ⚽ AUTONOMOUS BALL FOLLOWER:
       - Subscribes to /ball_position (Camera-LiDAR synchronized 3D point).
       - Real-time telemetry: Distance (meters), Bearing (degrees), Status.
       - Closed-loop steering and forward drive with proximity brake (<= 0.35m).
       - One-click toggle button [▶ START BALL FOLLOWER] or hotkey 'F'.
       - Instant manual override on any manual key press or Space bar.
====================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time
import math
import serial
import serial.tools.list_ports

try:
    import rclpy
    from rclpy.node import Node as RosNode
    from geometry_msgs.msg import Point as RosPoint
    HAS_ROS2 = True
except ImportError:
    HAS_ROS2 = False


class UniversalRobotTeleopGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚽ SOCCER BOT - MOTOR CONTROLLER & BALL FOLLOWER")
        self.root.geometry("540x800")
        self.root.configure(bg="#121216")
        self.root.resizable(False, False)
        
        self.sock = None
        self.ser = None
        self.connection_mode = "WIFI"  # "WIFI" or "USB"
        self.closing = False

        # Ball tracking telemetry state
        self.latest_ball_x = -1.0
        self.latest_ball_y = -1.0
        self.latest_ball_dist = -1.0
        self.latest_ball_time = 0.0
        self.ball_follower_active = False

        # Title Banner
        title_lbl = tk.Label(root, text="SOCCER BOT MOTOR CONTROLLER", font=("Segoe UI", 16, "bold"), fg="#00e5ff", bg="#121216")
        title_lbl.pack(pady=4)

        # Connection Mode Frame
        conn_frame = tk.LabelFrame(root, text=" 📡 Connection Setup ", font=("Segoe UI", 9, "bold"), fg="#ffd600", bg="#1a1a24", bd=1)
        conn_frame.pack(fill="x", padx=25, pady=3)

        # Wi-Fi Row
        wifi_row = tk.Frame(conn_frame, bg="#1a1a24")
        wifi_row.pack(fill="x", padx=8, pady=3)
        tk.Label(wifi_row, text="Robot IP:", font=("Segoe UI", 9, "bold"), fg="white", bg="#1a1a24").pack(side="left")
        self.ip_entry = tk.Entry(wifi_row, font=("Segoe UI", 10), width=16, bg="#2a2a38", fg="#00e5ff", insertbackground="white")
        self.ip_entry.insert(0, "192.168.0.135")
        self.ip_entry.pack(side="left", padx=6)
        
        self.btn_wifi_connect = tk.Button(wifi_row, text="Connect Wi-Fi", font=("Segoe UI", 9, "bold"), bg="#0288d1", fg="white",
                                          command=self.connect_wifi, relief="flat", cursor="hand2")
        self.btn_wifi_connect.pack(side="left", padx=4)

        # USB Serial Row
        usb_row = tk.Frame(conn_frame, bg="#1a1a24")
        usb_row.pack(fill="x", padx=8, pady=3)
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
        self.status_lbl.pack(pady=2)

        # Mode Indicator
        self.mode_lbl = tk.Label(root, text="Current Action: STOPPED", font=("Segoe UI", 11, "bold"), fg="#757575", bg="#121216")
        self.mode_lbl.pack(pady=2)

        # ==================== ⚽ AUTONOMOUS BALL FOLLOWER PANEL ====================
        follower_frame = tk.LabelFrame(root, text=" ⚽ AUTONOMOUS BALL FOLLOWER (LIDAR-SYNC) ",
                                       font=("Segoe UI", 9, "bold"), fg="#00e5ff", bg="#1a1a24", bd=1)
        follower_frame.pack(fill="x", padx=25, pady=4)

        # Telemetry row
        self.ball_telemetry_lbl = tk.Label(follower_frame, text="Ball: SCANNING... | Dist: --- | Bearing: ---",
                                           font=("Segoe UI", 9, "bold"), fg="#ffd600", bg="#1a1a24")
        self.ball_telemetry_lbl.pack(pady=3)

        self.follower_action_lbl = tk.Label(follower_frame, text="MODE: MANUAL CONTROL (IDLE)",
                                            font=("Segoe UI", 9, "bold"), fg="#757575", bg="#1a1a24")
        self.follower_action_lbl.pack(pady=2)

        # Large Toggle Button
        self.btn_follower_toggle = tk.Button(
            follower_frame, text="⚽ START BALL FOLLOWER (Press F)",
            font=("Segoe UI", 11, "bold"), bg="#2e7d32", fg="white",
            activebackground="#43a047", relief="flat", cursor="hand2",
            command=self.toggle_ball_follower
        )
        self.btn_follower_toggle.pack(fill="x", padx=16, pady=6)
        # =========================================================================

        # Speed Control Section
        speed_frame = tk.Frame(root, bg="#1a1a24", bd=1, relief="solid")
        speed_frame.pack(fill="x", padx=25, pady=4)

        header_box = tk.Frame(speed_frame, bg="#1a1a24")
        header_box.pack(fill="x", padx=10, pady=2)
        
        tk.Label(header_box, text="⚡ MOTOR SPEED (PWM)", font=("Segoe UI", 10, "bold"), fg="#ffd600", bg="#1a1a24").pack(side="left")
        self.speed_display = tk.Label(header_box, text="180 / 255 (Level 3)", font=("Segoe UI", 10, "bold"), fg="#00e5ff", bg="#1a1a24")
        self.speed_display.pack(side="right")
        
        slider_box = tk.Frame(speed_frame, bg="#1a1a24")
        slider_box.pack(fill="x", padx=10, pady=3)

        self.speed_val = tk.IntVar(value=180)
        self.speed_slider = tk.Scale(slider_box, from_=90, to=255, orient="horizontal", variable=self.speed_val,
                                     bg="#1a1a24", fg="#00e5ff", highlightthickness=0, font=("Segoe UI", 9, "bold"),
                                     troughcolor="#2a2a38", activebackground="#00e5ff", showvalue=False,
                                     command=self.update_slider_label)
        self.speed_slider.pack(fill="x", expand=True)

        # Speed Presets
        presets_box = tk.Frame(speed_frame, bg="#1a1a24")
        presets_box.pack(fill="x", padx=10, pady=3)
        
        tk.Button(presets_box, text="1: Slow (100)", bg="#37474f", fg="white", font=("Segoe UI", 8, "bold"),
                  command=lambda: self.set_preset(100), relief="flat", cursor="hand2").pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(presets_box, text="2: Normal (135)", bg="#37474f", fg="white", font=("Segoe UI", 8, "bold"),
                  command=lambda: self.set_preset(135), relief="flat", cursor="hand2").pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(presets_box, text="3: Medium (175)", bg="#37474f", fg="white", font=("Segoe UI", 8, "bold"),
                  command=lambda: self.set_preset(175), relief="flat", cursor="hand2").pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(presets_box, text="4: Fast (215)", bg="#37474f", fg="white", font=("Segoe UI", 8, "bold"),
                  command=lambda: self.set_preset(215), relief="flat", cursor="hand2").pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(presets_box, text="5: Max (255)", bg="#37474f", fg="white", font=("Segoe UI", 8, "bold"),
                  command=lambda: self.set_preset(255), relief="flat", cursor="hand2").pack(side="left", padx=2, expand=True, fill="x")

        # Control Buttons Frame
        btn_frame = tk.Frame(root, bg="#121216")
        btn_frame.pack(pady=4)

        btn_style = {"font": ("Segoe UI", 11, "bold"), "width": 11, "height": 2, "relief": "flat", "cursor": "hand2"}

        # UP (Forward)
        self.btn_fwd = tk.Button(btn_frame, text="▲\nFORWARD (W)", bg="#2e7d32", fg="white", activebackground="#43a047",
                                 command=lambda: self.drive_action('F', manual=True), **btn_style)
        self.btn_fwd.grid(row=0, column=1, padx=5, pady=3)

        # LEFT
        self.btn_left = tk.Button(btn_frame, text="◀\nSPIN LEFT (A)", bg="#1565c0", fg="white", activebackground="#1e88e5",
                                  command=lambda: self.drive_action('L', manual=True), **btn_style)
        self.btn_left.grid(row=1, column=0, padx=5, pady=3)

        # STOP (Space)
        self.btn_stop = tk.Button(btn_frame, text="⏹\nSTOP (Space)", bg="#c62828", fg="white", activebackground="#e53935",
                                  command=lambda: self.drive_action('S', manual=True), **btn_style)
        self.btn_stop.grid(row=1, column=1, padx=5, pady=3)

        # RIGHT
        self.btn_right = tk.Button(btn_frame, text="▶\nSPIN RIGHT (D)", bg="#1565c0", fg="white", activebackground="#1e88e5",
                                   command=lambda: self.drive_action('R', manual=True), **btn_style)
        self.btn_right.grid(row=1, column=2, padx=5, pady=3)

        # DOWN (Backward)
        self.btn_bwd = tk.Button(btn_frame, text="▼\nBACK (S)", bg="#d84315", fg="white", activebackground="#f4511e",
                                 command=lambda: self.drive_action('B', manual=True), **btn_style)
        self.btn_bwd.grid(row=2, column=1, padx=5, pady=3)

        # Instructions Footer
        footer = tk.Label(root, text="Keyboard: [W] Forward | [S] Back | [A] Left | [D] Right | [F] Follow Ball | [Space] STOP",
                          font=("Segoe UI", 9), fg="#757575", bg="#121216", justify="center")
        footer.pack(pady=3)

        # Key Bindings
        self.root.bind('<KeyPress-w>', lambda e: self.drive_action('F', manual=True))
        self.root.bind('<KeyPress-W>', lambda e: self.drive_action('F', manual=True))
        self.root.bind('<KeyPress-Up>', lambda e: self.drive_action('F', manual=True))

        self.root.bind('<KeyPress-s>', lambda e: self.drive_action('B', manual=True))
        self.root.bind('<KeyPress-S>', lambda e: self.drive_action('B', manual=True))
        self.root.bind('<KeyPress-Down>', lambda e: self.drive_action('B', manual=True))

        self.root.bind('<KeyPress-a>', lambda e: self.drive_action('L', manual=True))
        self.root.bind('<KeyPress-A>', lambda e: self.drive_action('L', manual=True))
        self.root.bind('<KeyPress-Left>', lambda e: self.drive_action('L', manual=True))

        self.root.bind('<KeyPress-d>', lambda e: self.drive_action('R', manual=True))
        self.root.bind('<KeyPress-D>', lambda e: self.drive_action('R', manual=True))
        self.root.bind('<KeyPress-Right>', lambda e: self.drive_action('R', manual=True))

        self.root.bind('<KeyPress-f>', lambda e: self.toggle_ball_follower())
        self.root.bind('<KeyPress-F>', lambda e: self.toggle_ball_follower())

        self.root.bind('<space>', lambda e: self.stop_all())
        self.root.bind('<KeyPress-x>', lambda e: self.stop_all())

        # Auto-try Wi-Fi connect in background on startup
        threading.Thread(target=self.connect_wifi, daemon=True).start()

        # Start ROS 2 Ball Position listener in background
        if HAS_ROS2:
            threading.Thread(target=self.ros2_ball_listener_thread, daemon=True).start()

        # GUI Telemetry refresh timer
        self.schedule_telemetry_check()

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
        except Exception:
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

    def ros2_ball_listener_thread(self):
        """Background thread listening to ROS 2 topic /ball_position."""
        try:
            if not rclpy.ok():
                rclpy.init()
            node = RosNode('gui_ball_telemetry_listener')

            def ball_cb(msg: RosPoint):
                self.latest_ball_x = msg.x
                self.latest_ball_y = msg.y
                self.latest_ball_dist = msg.z
                self.latest_ball_time = time.time()

            sub = node.create_subscription(RosPoint, '/ball_position', ball_cb, 10)
            while not self.closing and rclpy.ok():
                rclpy.spin_once(node, timeout_sec=0.1)
            node.destroy_node()
        except Exception as e:
            print(f"[GUI ROS2] Listener exception: {e}")

    def schedule_telemetry_check(self):
        """Update GUI telemetry labels every 100ms."""
        if self.closing:
            return
        now = time.time()
        if (now - self.latest_ball_time) < 1.2 and self.latest_ball_dist > 0:
            dist = self.latest_ball_dist
            lat = self.latest_ball_y
            fwd = max(0.01, self.latest_ball_x)
            deg = math.degrees(math.atan2(lat, fwd))
            side_str = "LEFT" if lat > 0.05 else ("RIGHT" if lat < -0.05 else "AHEAD")
            self.ball_telemetry_lbl.config(
                text=f"⚽ Ball: TRACKED | Dist: {dist:.2f} m | Bearing: {deg:+.1f}° ({side_str})",
                fg="#00e676"
            )
        else:
            self.ball_telemetry_lbl.config(
                text="⚽ Ball: SEARCHING... (Move ball into camera/LiDAR view)",
                fg="#ffd600"
            )
        self.root.after(100, self.schedule_telemetry_check)

    def toggle_ball_follower(self):
        """Toggle autonomous ball following mode."""
        self.ball_follower_active = not self.ball_follower_active
        if self.ball_follower_active:
            self.btn_follower_toggle.config(
                text="⏹ STOP BALL FOLLOWER (Press Space)", bg="#c62828", activebackground="#e53935")
            self.follower_action_lbl.config(text="MODE: AUTONOMOUS BALL CHASER ACTIVE", fg="#00e676")
            threading.Thread(target=self.ball_follower_loop, daemon=True).start()
        else:
            self.btn_follower_toggle.config(
                text="⚽ START BALL FOLLOWER (Press F)", bg="#2e7d32", activebackground="#43a047")
            self.follower_action_lbl.config(text="MODE: MANUAL CONTROL (IDLE)", fg="#757575")
            self.drive_action('S', manual=False)

    def ball_follower_loop(self):
        """Closed-loop control: steers toward ball and stops within 35 cm."""
        while self.ball_follower_active and not self.closing:
            now = time.time()
            if (now - self.latest_ball_time) < 1.2 and self.latest_ball_dist > 0:
                dist = self.latest_ball_dist
                lat = self.latest_ball_y

                # Stop distance threshold (0.35m = ~14 inches)
                if dist <= 0.35:
                    self.drive_action('S', manual=False)
                    self.follower_action_lbl.config(
                        text=f"🎯 BALL REACHED ({dist:.2f}m)! STOPPED READY TO KICK", fg="#00e676")
                else:
                    if lat > 0.12:
                        # Ball to the left -> Steer left
                        self.drive_action('L', manual=False)
                        self.follower_action_lbl.config(
                            text=f"🔄 ALIGNING: Turning Left (Dist: {dist:.2f}m, y: {lat:+.2f}m)", fg="#00e5ff")
                    elif lat < -0.12:
                        # Ball to the right -> Steer right
                        self.drive_action('R', manual=False)
                        self.follower_action_lbl.config(
                            text=f"🔄 ALIGNING: Turning Right (Dist: {dist:.2f}m, y: {lat:+.2f}m)", fg="#00e5ff")
                    else:
                        # Ball centered -> Drive forward!
                        self.drive_action('F', manual=False)
                        self.follower_action_lbl.config(
                            text=f"🚀 CHASE: Driving Forward to Ball ({dist:.2f}m)", fg="#00e676")
            else:
                # No ball in view -> hold or gentle search
                self.drive_action('S', manual=False)
                self.follower_action_lbl.config(text="🔍 SEARCHING: No Ball In Sight", fg="#ffd600")

            time.sleep(0.08)

    def stop_all(self):
        """Emergency stop: stops motors and disengages autonomous follower."""
        if self.ball_follower_active:
            self.ball_follower_active = False
            self.btn_follower_toggle.config(
                text="⚽ START BALL FOLLOWER (Press F)", bg="#2e7d32", activebackground="#43a047")
            self.follower_action_lbl.config(text="MODE: MANUAL OVERRIDE (STOPPED)", fg="#ff5252")
        self.drive_action('S', manual=True)

    def drive_action(self, action, manual=True):
        if manual and self.ball_follower_active and action != 'S':
            # Manual override immediately cancels auto follower
            self.ball_follower_active = False
            self.btn_follower_toggle.config(
                text="⚽ START BALL FOLLOWER (Press F)", bg="#2e7d32", activebackground="#43a047")
            self.follower_action_lbl.config(text="MODE: MANUAL OVERRIDE (AUTO STOPPED)", fg="#ffd600")

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
        prefix = "[MANUAL]" if manual else "[AUTO]"
        self.mode_lbl.config(text=f"{prefix} Action: {name} (PWM: {spd})", fg=col)

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
                        except Exception:
                            pass

        threading.Thread(target=_send, daemon=True).start()

    def on_closing(self):
        self.closing = True
        self.ball_follower_active = False
        try:
            if self.sock:
                self.sock.sendall(b"SET:0,0\n")
                self.sock.close()
            if self.ser and self.ser.is_open:
                self.ser.write(b'S')
                self.ser.close()
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = UniversalRobotTeleopGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()
