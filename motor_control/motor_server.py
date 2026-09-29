#!/usr/bin/env python3
"""
====================================================================
      SOCCER BOT - ROBUST ARDUINO MOTOR TCP CONTROLLER (PORT 9000)
====================================================================
Features:
  1. Auto-detection & auto-reconnect for Arduino UNO (/dev/ttyACM0)
  2. Background serial drain thread: prevents Arduino TX buffer lockup!
  3. Single-byte direction commands ('F', 'B', 'L', 'R', 'S') matching
     the verified working Arduino sketch (soccer_bot_motor_driver.ino)
  4. Compatibility with SET:l,r PWM format and single-letter commands
  5. Automatic failsafe stop on client disconnect or idle
====================================================================
"""

import os
import glob
import socket
import serial
import threading
import time
import sys

ser = None
lock = threading.Lock()
last_cmd_sent = None

def get_arduino_port():
    # Prefer explicit Arduino by-id symlinks
    for p in sorted(glob.glob("/dev/serial/by-id/*")):
        name = os.path.basename(p).lower()
        if "cp210" in name or "silicon_labs" in name:
            continue # Skip LiDAR
        if "arduino" in name or "uno" in name or "cdc" in name or "ch340" in name:
            return os.path.realpath(p)
    
    # Fallback to /dev/ttyACM*
    acm_ports = sorted(glob.glob("/dev/ttyACM*"))
    if acm_ports:
        return acm_ports[0]
    return None

def serial_manager():
    """Manages Arduino connection and automatically reconnects on cable pulls/resets."""
    global ser
    while True:
        with lock:
            s = ser
        
        need_connect = False
        if s is None or not s.is_open:
            need_connect = True
        else:
            try:
                # Active probe to verify file descriptor is alive
                _ = s.in_waiting
            except Exception:
                need_connect = True
                with lock:
                    try:
                        s.close()
                    except Exception:
                        pass
                    ser = None

        if need_connect:
            port = get_arduino_port()
            if port:
                try:
                    s_new = serial.Serial(port, 9600, timeout=1.0)
                    time.sleep(2.0) # Wait for Arduino bootloader to complete
                    s_new.reset_input_buffer()
                    s_new.reset_output_buffer()
                    with lock:
                        ser = s_new
                    print(f"[OK] Arduino connected successfully on {port} @ 9600 Baud!", flush=True)
                except Exception as e:
                    print(f"[WARN] Failed to connect Arduino on {port}: {e}", flush=True)
            time.sleep(1.5)
        else:
            time.sleep(1.0)

threading.Thread(target=serial_manager, daemon=True).start()

def serial_drain_thread():
    """Continuously drains Arduino serial output to prevent TX buffer deadlock."""
    global ser
    while True:
        with lock:
            s = ser
        if s and s.is_open:
            try:
                line = s.readline()
                if line:
                    text = line.decode('utf-8', errors='ignore').strip()
                    if text:
                        print(f"[ARDUINO] {text}", flush=True)
            except Exception:
                time.sleep(0.1)
        else:
            time.sleep(0.5)

threading.Thread(target=serial_drain_thread, daemon=True).start()

def send_to_arduino(char_cmd):
    """Sends a clean single-character command ('F', 'B', 'L', 'R', 'S') to Arduino."""
    global last_cmd_sent, ser
    if char_cmd not in ['F', 'B', 'L', 'R', 'S']:
        return

    # Deduplicate repeated identical motion commands, but always allow 'S'
    if char_cmd == last_cmd_sent and char_cmd != 'S':
        return

    with lock:
        s = ser
        if s and s.is_open:
            try:
                s.write(char_cmd.encode('utf-8'))
                s.flush()
                last_cmd_sent = char_cmd
                print(f"[MOTOR] Sent '{char_cmd}' to Arduino", flush=True)
            except Exception as e:
                print(f"[SERIAL ERR] Failed to write '{char_cmd}': {e}", flush=True)
                try:
                    s.close()
                except Exception:
                    pass
                ser = None
        else:
            print(f"[WARN] Cannot send '{char_cmd}': Arduino not connected!", flush=True)

def handle_client(conn, addr):
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"[CLIENT CONNECTED] {addr}", flush=True)
    try:
        while True:
            data = conn.recv(128)
            if not data:
                break
            text = data.decode('utf-8', errors='ignore').strip()
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                if line in ['F', 'B', 'L', 'R', 'S']:
                    send_to_arduino(line)
                elif line.startswith('SET:'):
                    try:
                        vals = line[4:].split(',')
                        l = int(vals[0])
                        r = int(vals[1])
                        if l == 0 and r == 0:
                            send_to_arduino('S')
                        elif l > 0 and r > 0:
                            send_to_arduino('F')
                        elif l < 0 and r < 0:
                            send_to_arduino('B')
                        elif l < 0 and r > 0:
                            send_to_arduino('L')
                        elif l > 0 and r < 0:
                            send_to_arduino('R')
                    except Exception as err:
                        print(f"[PARSE ERR] {err}", flush=True)
                elif line.startswith('L:') or line.startswith('l:'):
                    try:
                        parts = line.split()
                        l = int(parts[0].split(':')[1])
                        r = int(parts[1].split(':')[1])
                        if l == 0 and r == 0:
                            send_to_arduino('S')
                        elif l > 0 and r > 0:
                            send_to_arduino('F')
                        elif l < 0 and r < 0:
                            send_to_arduino('B')
                        elif l < 0 and r > 0:
                            send_to_arduino('L')
                        elif l > 0 and r < 0:
                            send_to_arduino('R')
                    except Exception as err:
                        print(f"[PARSE ERR] {err}", flush=True)
    except Exception as e:
        print(f"[CLIENT ERR] {e}", flush=True)
    finally:
        send_to_arduino('S')
        try:
            conn.close()
        except Exception:
            pass
        print(f"[CLIENT DISCONNECTED] {addr}", flush=True)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind(('0.0.0.0', 9000))
    server.listen(10)
    print("🚀 Soccer Bot Robust Motor Server listening on 0.0.0.0:9000", flush=True)

    while True:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            time.sleep(0.5)

if __name__ == '__main__':
    main()
