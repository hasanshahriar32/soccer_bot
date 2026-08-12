#!/usr/bin/env python3
"""
====================================================================
      SOCCER BOT - UNIVERSAL AUTO-ADAPTIVE MOTOR SERVER (PORT 9000)
====================================================================
"""

import socket
import serial
import threading
import time
import sys

# Tuned Speeds: Smooth forward/reverse and gentle, controlled spin
SPEED_FORWARD  = (180, 180)
SPEED_BACKWARD = (-180, -180)
SPEED_LEFT     = (-135, 135) # Gentle, controlled spin
SPEED_RIGHT    = (135, -135) # Gentle, controlled spin
SPEED_STOP     = (0, 0)

current_target = SPEED_STOP
lock = threading.Lock()
ser = None

def init_serial():
    global ser
    ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    for baud in [115200, 9600]:
        for p in ports:
            try:
                s = serial.Serial(p, baud, timeout=0.1)
                time.sleep(1.5)
                s.reset_input_buffer()
                s.reset_output_buffer()
                print(f"[OK] Opened {p} @ {baud} Baud!", flush=True)
                ser = s
                return True
            except Exception as e:
                pass
    return False

if not init_serial():
    print("[ERROR] Could not open any serial port on Pi!", flush=True)
    sys.exit(1)

def streaming_worker():
    global current_target
    while True:
        try:
            with lock:
                left, right = current_target
                if ser and ser.is_open:
                    packet = f"L:{left} R:{right}\n".encode()
                    ser.write(packet)
                    ser.flush()
        except Exception as e:
            print(f"[SERIAL ERR] {e}", flush=True)
        time.sleep(0.04) # 25 Hz

threading.Thread(target=streaming_worker, daemon=True).start()

def handle_client(conn, addr):
    global current_target
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"[CLIENT CONNECTED] {addr}", flush=True)
    try:
        while True:
            data = conn.recv(64)
            if not data:
                break
            text = data.decode('utf-8', errors='ignore').strip()
            
            # Support custom speed packets like "L:120 R:120" or single chars
            if text.startswith('L:') or text.startswith('l:'):
                try:
                    parts = text.split()
                    l_val = int(parts[0].split(':')[1])
                    r_val = int(parts[1].split(':')[1])
                    with lock:
                        current_target = (l_val, r_val)
                except:
                    pass
            else:
                for ch in text.upper():
                    with lock:
                        if ch == 'F':
                            current_target = SPEED_FORWARD
                        elif ch == 'B':
                            current_target = SPEED_BACKWARD
                        elif ch == 'L':
                            current_target = SPEED_LEFT
                        elif ch == 'R':
                            current_target = SPEED_RIGHT
                        elif ch == 'S':
                            current_target = SPEED_STOP
                    print(f"[ACTION] Executed '{ch}' -> Left={current_target[0]}, Right={current_target[1]}", flush=True)
    except Exception as e:
        print(f"[CLIENT ERR] {e}", flush=True)
    finally:
        conn.close()
        print(f"[CLIENT DISCONNECTED] {addr}", flush=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
server.bind(('0.0.0.0', 9000))
server.listen(10)
print("[3] Universal Motor Server listening on 0.0.0.0:9000 (Port Ready!)...", flush=True)

while True:
    try:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as err:
        print(f"[SERVER ERR] {err}", flush=True)
        time.sleep(0.5)
