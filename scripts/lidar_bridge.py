#!/usr/bin/env python3
"""
====================================================================
      SOCCER BOT - YDLIDAR SERIAL-TO-TCP DTR-ENABLED BRIDGE (PORT 5000)
====================================================================
Powers the YDLidar motor via DTR=True, issues the STOP-SCAN reset
handshake (0xA5 0x65), and provides a low-latency bidirectional TCP
stream for the ROS 2 YDLidar driver on the laptop.
====================================================================
"""

import socket
import serial
import threading
import time
import sys
import os
import glob

def get_lidar_port():
    cp210_by_id = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"
    if os.path.exists(cp210_by_id):
        return cp210_by_id
    for p in glob.glob("/dev/serial/by-id/*"):
        if "cp210" in p.lower() or "silicon" in p.lower():
            return p
    if os.path.exists("/dev/ttyUSB1"):
        return "/dev/ttyUSB1"
    return "/dev/ttyUSB1"

def main():
    baud = 115200
    lidar_port = get_lidar_port()
    try:
        ser = serial.Serial(lidar_port, baud, timeout=0.05)
        ser.setDTR(True)
        ser.setRTS(True)
        time.sleep(0.5)
        
        # Stop any active scanning so device info / health check succeeds
        ser.write(b'\xa5\x65')
        time.sleep(0.3)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print(f"[LIDAR BRIDGE] Opened {lidar_port} with DTR=True & RTS=True", flush=True)
    except Exception as e:
        print(f"[LIDAR BRIDGE ERR] Failed to open {lidar_port}: {e}", flush=True)
        sys.exit(1)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    server.bind(('0.0.0.0', 5000))
    server.listen(1)
    print("[LIDAR BRIDGE] Listening on 0.0.0.0:5000...", flush=True)

    while True:
        try:
            conn, addr = server.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"[LIDAR BRIDGE] Client connected: {addr}", flush=True)
            
            # Reset buffers for new session
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            running = True

            def tcp_to_ser():
                nonlocal running
                try:
                    while running:
                        data = conn.recv(2048)
                        if not data:
                            break
                        ser.write(data)
                except Exception:
                    pass
                finally:
                    running = False

            def ser_to_tcp():
                nonlocal running
                try:
                    while running:
                        n = ser.in_waiting
                        data = ser.read(max(1, min(n, 4096)))
                        if data:
                            conn.sendall(data)
                        else:
                            time.sleep(0.005)
                except Exception:
                    pass
                finally:
                    running = False

            t1 = threading.Thread(target=tcp_to_ser, daemon=True)
            t2 = threading.Thread(target=ser_to_tcp, daemon=True)
            t1.start()
            t2.start()

            while running:
                time.sleep(0.1)

            try:
                conn.close()
            except Exception:
                pass
            print(f"[LIDAR BRIDGE] Client disconnected: {addr}", flush=True)

        except Exception as e:
            print(f"[LIDAR BRIDGE ERR] {e}", flush=True)
            time.sleep(0.5)

if __name__ == '__main__':
    main()
