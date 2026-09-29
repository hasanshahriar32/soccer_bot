#!/usr/bin/env python3
"""
====================================================================
  SOCCER BOT - 4-DOF ROBOTIC ARM TCP SERVER (PORT 9001)
====================================================================
Listens on TCP port 9001. Connects to Arduino Uno/Nano on /dev/ttyUSB1.
====================================================================
"""

import os
import sys
import time
import socket
import threading
import json
import re
import serial

import glob

def get_arm_port():
    ch340_by_id = "/dev/serial/by-id/usb-1a86_USB2.0-Ser_-if00-port0"
    if os.path.exists(ch340_by_id):
        return ch340_by_id
    for p in glob.glob("/dev/serial/by-id/*"):
        name = os.path.basename(p).lower()
        if "1a86" in name or "ch340" in name:
            return p

    # Find and exclude LiDAR port (CP2102)
    lidar_target = None
    for p in glob.glob("/dev/serial/by-id/*cp210*"):
        try:
            lidar_target = os.path.realpath(p)
        except Exception:
            pass

    for candidate in ["/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyUSB3"]:
        if os.path.exists(candidate):
            try:
                if lidar_target and os.path.realpath(candidate) == lidar_target:
                    continue
            except Exception:
                pass
            return candidate
    return None

ARM_BAUD = 9600
TCP_PORT = 9001

class ArmController:
    def __init__(self, port=None, baud=ARM_BAUD):
        self.port = port or get_arm_port()
        self.baud = baud
        self.ser = None
        self.lock = threading.RLock()
        
        self.base = 0
        self.shoulder = 0
        self.albo = 0
        self.gripper = 90
        self.last_update = 0.0
        self.connected = False
        
        self.connect()

    def connect(self):
        with self.lock:
            self.port = get_arm_port()
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.connected = False
            if not self.port:
                print("[ARM] No Hand Arduino serial port detected (CH340). Waiting for connection...", flush=True)
                return
            for attempt in range(2):
                try:
                    print(f"[ARM] Opening serial port {self.port} @ {self.baud} baud (attempt {attempt+1})...", flush=True)
                    self.ser = serial.Serial(self.port, self.baud, timeout=0.2)
                    time.sleep(2.5)
                    # Drain startup boot messages safely without calling reset_input_buffer
                    while self.ser.in_waiting:
                        self.ser.read(self.ser.in_waiting)
                        time.sleep(0.05)
                        
                    self.connected = True
                    print(f"[ARM] Connected to Arduino Arm Controller on {self.port}!", flush=True)
                    
                    self._send_raw("STATUS\n")
                    lines = self._read_lines(timeout=2.0)
                    for l in lines:
                        self._parse_status_line(l)
                    break
                except Exception as e:
                    print(f"[ARM ERROR] Serial connection failed: {e}", flush=True)
                    self.ser = None
                    self.connected = False
                    time.sleep(1.0)

    def _send_raw(self, cmd_str):
        if not cmd_str.endswith('\n'):
            cmd_str += '\n'
        try:
            if self.ser and self.ser.is_open:
                self.ser.reset_input_buffer()
        except Exception:
            pass
        print(f"[ARM RAW SEND] {cmd_str.strip()}", flush=True)
        self.ser.write(cmd_str.encode('utf-8'))
        self.ser.flush()

    def _read_lines(self, timeout=3.5):
        lines = []
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.ser and self.ser.is_open:
                try:
                    if self.ser.in_waiting:
                        line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            print(f"[ARM RAW RECV] {line}", flush=True)
                            lines.append(line)
                            if ("OK" in line or "ERR" in line or "ARM_STATUS" in line or 
                                "Pulse =" in line or "deg" in line or line.startswith("::")):
                                break
                    else:
                        time.sleep(0.02)
                except Exception as e:
                    print(f"[ARM ERROR] Readline error: {e}", flush=True)
                    break
            else:
                break
        return lines

    def _parse_status_line(self, line):
        if "B:" in line and "S:" in line and "A:" in line and "G:" in line:
            try:
                parts = line.split()
                for p in parts:
                    if p.startswith("B:"):
                        self.base = int(p.split(":")[1])
                    elif p.startswith("S:"):
                        self.shoulder = int(p.split(":")[1])
                    elif p.startswith("A:"):
                        self.albo = int(p.split(":")[1])
                    elif p.startswith("G:"):
                        self.gripper = int(p.split(":")[1])
                self.last_update = time.time()
            except Exception:
                pass

    def send_command(self, cmd_str):
        with self.lock:
            if not self.connected or not self.ser or not self.ser.is_open:
                self.connect()
                if not self.connected:
                    return {"status": "ERR", "msg": "Serial disconnected"}

            try:
                cmd_upper = cmd_str.upper().strip()
                if cmd_upper in ["GRAB", "CLOSE"]:
                    cmd_str = "G 90"
                elif cmd_upper == "OPEN":
                    cmd_str = "G 270"

                # Keep local state in sync with requested position
                parts = cmd_str.strip().split()
                if len(parts) >= 2:
                    try:
                        j_prefix = parts[0].upper()
                        val = int(parts[1])
                        if j_prefix == "B": self.base = val
                        elif j_prefix == "S": self.shoulder = val
                        elif j_prefix in ("A", "E"): self.albo = val
                        elif j_prefix == "G": self.gripper = val
                    except Exception:
                        pass

                self._send_raw(cmd_str)
                timeout = 15.0 if "TEST" in cmd_str.upper() else 3.5
                lines = self._read_lines(timeout=timeout)
                resp_text = " ".join(lines) if lines else "OK"
                
                for l in lines:
                    self._parse_status_line(l)
                    m = re.search(r'B:(\d+)', l)
                    if m: self.base = int(m.group(1))
                    m = re.search(r'S:(\d+)', l)
                    if m: self.shoulder = int(m.group(1))
                    m = re.search(r'A:(\d+)', l)
                    if m: self.albo = int(m.group(1))
                    m = re.search(r'G:(\d+)', l)
                    if m: self.gripper = int(m.group(1))
                    m = re.search(r'Gripper\s*=\s*(\d+)', l)
                    if m: self.gripper = int(m.group(1))
                    
                    if "HOME" in l:
                        self.base = 0
                        self.shoulder = 0
                        self.albo = 0
                        self.gripper = 90
                    elif "READY" in l:
                        self.base = 90
                        self.shoulder = 70
                        self.albo = 80
                        self.gripper = 240
                    elif "GRAB" in l or "CLOSE" in l:
                        self.gripper = 90
                    elif "OPEN" in l:
                        self.gripper = 270

                self.last_update = time.time()
                return {
                    "status": "OK",
                    "response": resp_text,
                    "base": self.base,
                    "shoulder": self.shoulder,
                    "albo": self.albo,
                    "gripper": self.gripper,
                    "connected": self.connected
                }
            except Exception as e:
                print(f"[ARM ERROR] Execution error: {e}", flush=True)
                self.connected = False
                try:
                    if self.ser:
                        self.ser.close()
                except Exception:
                    pass
                self.ser = None
                return {"status": "ERR", "msg": str(e)}

    def get_status(self):
        with self.lock:
            return {
                "status": "OK",
                "base": self.base,
                "shoulder": self.shoulder,
                "albo": self.albo,
                "gripper": self.gripper,
                "connected": self.connected,
                "timestamp": self.last_update
            }

arm = ArmController()

def handle_client(conn, addr):
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    buffer = ""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data.decode('utf-8', errors='ignore')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue

                resp = None
                if line.startswith('{') and line.endswith('}'):
                    try:
                        req = json.loads(line)
                        act = req.get("action", "").lower()
                        if act == "status":
                            resp = arm.get_status()
                        elif act == "home":
                            resp = arm.send_command("HOME")
                        elif act == "ready":
                            resp = arm.send_command("READY")
                        elif act == "grab" or act == "close":
                            resp = arm.send_command("G 90")
                        elif act == "open":
                            resp = arm.send_command("G 270")
                        elif act == "pickup":
                            # Automated smooth pickup sequence per user specs
                            arm.send_command("G 270") # Open gripper
                            time.sleep(1.0)
                            arm.send_command("S 70")  # Lower shoulder
                            arm.send_command("A 80")  # Lower elbow
                            time.sleep(1.5)
                            arm.send_command("G 90")  # Grip ball
                            time.sleep(1.2)
                            arm.send_command("S 0")   # Lift shoulder
                            arm.send_command("A 0")   # Lift elbow
                            resp = arm.get_status()
                        elif act == "test":
                            resp = arm.send_command("TEST")
                        elif act == "joint":
                            joint = req.get("joint", "").upper()
                            ang = int(req.get("angle", 0))
                            resp = arm.send_command(f"{joint} {ang}")
                        else:
                            resp = {"status": "ERR", "msg": f"Unknown action: {act}"}
                    except Exception as e:
                        resp = {"status": "ERR", "msg": f"JSON parse error: {e}"}
                else:
                    cmd = line.upper()
                    if cmd == "STATUS" or cmd == "?":
                        resp = arm.get_status()
                    else:
                        resp = arm.send_command(cmd)

                out_str = json.dumps(resp) + "\n"
                conn.sendall(out_str.encode('utf-8'))
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind(('0.0.0.0', TCP_PORT))
    server.listen(10)
    print("=" * 60)
    print(f"   🦾 SOCCER BOT ROBOTIC ARM SERVER LISTENING ON 0.0.0.0:{TCP_PORT}")
    print(f"   Serial Link: {arm.port} @ {ARM_BAUD} Baud")
    print("=" * 60, flush=True)

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

if __name__ == '__main__':
    main()
