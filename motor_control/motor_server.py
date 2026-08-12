#!/usr/bin/env python3
"""
====================================================================
      SOCCER BOT - DYNAMIC VARIABLE SPEED MOTOR SERVER (PORT 9000)
====================================================================
"""

import socket
import serial
import threading
import time
import sys

current_left = 0
current_right = 0
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
    global current_left, current_right
    while True:
        try:
            with lock:
                l, r = current_left, current_right
                if ser and ser.is_open:
                    packet = f"L:{l} R:{r}\n".encode()
                    ser.write(packet)
                    ser.flush()
        except Exception as e:
            print(f"[SERIAL ERR] {e}", flush=True)
        time.sleep(0.04) # 25 Hz

threading.Thread(target=streaming_worker, daemon=True).start()

def handle_client(conn, addr):
    global current_left, current_right
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"[CLIENT CONNECTED] {addr}", flush=True)
    try:
        while True:
            data = conn.recv(128)
            if not data:
                break
            text = data.decode('utf-8', errors='ignore').strip()
            
            # Format: "SET:left_pwm,right_pwm" e.g. "SET:120,120"
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('SET:'):
                    try:
                        vals = line[4:].split(',')
                        l = int(vals[0])
                        r = int(vals[1])
                        with lock:
                            current_left = l
                            current_right = r
                        print(f"[ACTION] Dynamic PWM -> Left={l}, Right={r}", flush=True)
                    except Exception as err:
                        print(f"[PARSE ERR] {err}", flush=True)
                elif line.startswith('L:') or line.startswith('l:'):
                    try:
                        parts = line.split()
                        l = int(parts[0].split(':')[1])
                        r = int(parts[1].split(':')[1])
                        with lock:
                            current_left = l
                            current_right = r
                        print(f"[ACTION] L/R PWM -> Left={l}, Right={r}", flush=True)
                    except Exception as err:
                        print(f"[PARSE ERR] {err}", flush=True)
                elif line in ['F', 'B', 'L', 'R', 'S']:
                    with lock:
                        if line == 'F':
                            current_left, current_right = 200, 200
                        elif line == 'B':
                            current_left, current_right = -200, -200
                        elif line == 'L':
                            current_left, current_right = -170, 170
                        elif line == 'R':
                            current_left, current_right = 170, -170
                        elif line == 'S':
                            current_left, current_right = 0, 0
                    print(f"[ACTION] Char '{line}' -> Left={current_left}, Right={current_right}", flush=True)
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
print("[3] Universal Variable Speed Server listening on 0.0.0.0:9000...", flush=True)

while True:
    try:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as err:
        print(f"[SERVER ERR] {err}", flush=True)
        time.sleep(0.5)
