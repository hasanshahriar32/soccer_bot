#!/usr/bin/env python3
"""
====================================================================
      SOCCER BOT - 9600 BAUD COMPATIBLE MOTOR SERVER (PORT 9000)
====================================================================
Translates dynamic GUI speed commands into working single-character
commands ('F', 'B', 'L', 'R', 'S') at 9600 Baud.
====================================================================
"""

import socket
import serial
import threading
import time
import sys

# Track the last character command sent to prevent duplicates
last_cmd_sent = 'S'
lock = threading.Lock()
ser = None

def init_serial():
    global ser
    ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    # Force 9600 Baud to match the verified working sketch!
    for p in ports:
        try:
            s = serial.Serial(p, 9600, timeout=1.0)
            time.sleep(2.0)
            s.reset_input_buffer()
            s.reset_output_buffer()
            print(f"[OK] Opened {p} @ 9600 Baud!", flush=True)
            ser = s
            return True
        except Exception as e:
            pass
    return False

if not init_serial():
    print("[ERROR] Could not open any serial port on Pi!", flush=True)
    sys.exit(1)

def send_to_arduino(char_cmd):
    global last_cmd_sent
    try:
        with lock:
            if ser and ser.is_open:
                # Send the single-character command expected by the 9600 Baud sketch
                ser.write(char_cmd.encode('utf-8'))
                ser.flush()
                last_cmd_sent = char_cmd
                print(f"[SERIAL] Sent '{char_cmd}' to Arduino", flush=True)
    except Exception as e:
        print(f"[SERIAL ERR] {e}", flush=True)

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
                
                # Parse GUI "SET:left_pwm,right_pwm" and map to directions
                if line.startswith('SET:'):
                    try:
                        vals = line[4:].split(',')
                        l = int(vals[0])
                        r = int(vals[1])
                        
                        speed = max(abs(l), abs(r))
                        if speed > 0:
                            if speed < 115:
                                send_to_arduino('1')
                            elif speed < 155:
                                send_to_arduino('2')
                            elif speed < 195:
                                send_to_arduino('3')
                            elif speed < 235:
                                send_to_arduino('4')
                            else:
                                send_to_arduino('5')
                        
                        if l > 0 and r > 0:
                            send_to_arduino('F')
                        elif l < 0 and r < 0:
                            send_to_arduino('B')
                        elif l < 0 and r > 0:
                            send_to_arduino('L')
                        elif l > 0 and r < 0:
                            send_to_arduino('R')
                        else:
                            send_to_arduino('S')
                    except Exception as err:
                        print(f"[PARSE ERR] {err}", flush=True)
                elif line.startswith('L:') or line.startswith('l:'):
                    try:
                        parts = line.split()
                        l = int(parts[0].split(':')[1])
                        r = int(parts[1].split(':')[1])
                        
                        speed = max(abs(l), abs(r))
                        if speed > 0:
                            if speed < 115:
                                send_to_arduino('1')
                            elif speed < 155:
                                send_to_arduino('2')
                            elif speed < 195:
                                send_to_arduino('3')
                            elif speed < 235:
                                send_to_arduino('4')
                            else:
                                send_to_arduino('5')
                        
                        if l > 0 and r > 0:
                            send_to_arduino('F')
                        elif l < 0 and r < 0:
                            send_to_arduino('B')
                        elif l < 0 and r > 0:
                            send_to_arduino('L')
                        elif l > 0 and r < 0:
                            send_to_arduino('R')
                        else:
                            send_to_arduino('S')
                    except Exception as err:
                        print(f"[PARSE ERR] {err}", flush=True)
                elif line in ['F', 'B', 'L', 'R', 'S']:
                    send_to_arduino(line)
    except Exception as e:
        print(f"[CLIENT ERR] {e}", flush=True)
    finally:
        send_to_arduino('S')
        conn.close()
        print(f"[CLIENT DISCONNECTED] {addr}", flush=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
server.bind(('0.0.0.0', 9000))
server.listen(10)
print("[3] 9600 Baud Motor Server listening on 0.0.0.0:9000 (Universal Client Ready)...", flush=True)

while True:
    try:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as err:
        print(f"[SERVER ERR] {err}", flush=True)
        time.sleep(0.5)
