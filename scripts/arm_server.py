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
import serial

ARM_PORT = "/dev/ttyUSB1"
ARM_BAUD = 9600
TCP_PORT = 9001

class ArmController:
    def __init__(self, port=ARM_PORT, baud=ARM_BAUD):
        self.port = port
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
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.connected = False
            for attempt in range(2):
                try:
                    print(f"[ARM] Opening serial port {self.port} @ {self.baud} baud (attempt {attempt+1})...", flush=True)
                    self.ser = serial.Serial(self.port, self.baud, timeout=0.2)
                    time.sleep(2.2)
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
        print(f"[ARM RAW SEND] {cmd_str.strip()}", flush=True)
        self.ser.write(cmd_str.encode('utf-8'))
        self.ser.flush()

    def _read_lines(self, timeout=6.0):
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
                            if line.startswith("OK") or line.startswith("ERR") or line.startswith("ARM_STATUS"):
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
                self._send_raw(cmd_str)
                timeout = 15.0 if "TEST" in cmd_str.upper() else 6.0
                lines = self._read_lines(timeout=timeout)
                resp_text = " ".join(lines) if lines else "OK"
                
                for l in lines:
                    self._parse_status_line(l)
                    if l.startswith("OK B:"):
                        self.base = int(l.split(":")[1])
                    elif l.startswith("OK S:"):
                        self.shoulder = int(l.split(":")[1])
                    elif l.startswith("OK A:"):
                        self.albo = int(l.split(":")[1])
                    elif l.startswith("OK G:"):
                        self.gripper = int(l.split(":")[1])
                    elif "HOME" in l:
                        self.base = 0
                        self.shoulder = 0
                        self.albo = 0
                        self.gripper = 180
                    elif "READY" in l:
                        self.base = 90
                        self.shoulder = 70
                        self.albo = 80
                        self.gripper = 240
                    elif "GRAB" in l:
                        self.gripper = 125
                    elif "OPEN" in l:
                        self.gripper = 240

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
                        elif act == "grab":
                            resp = arm.send_command("GRAB")
                        elif act == "open":
                            resp = arm.send_command("OPEN")
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
    print(f"   Serial Link: {ARM_PORT} @ {ARM_BAUD} Baud")
    print("=" * 60, flush=True)

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()

if __name__ == '__main__':
    main()
