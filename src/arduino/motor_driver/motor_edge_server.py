#!/usr/bin/env python3
"""
motor_edge_server.py
Lightweight TCP socket server running on the Raspberry Pi.
Listens on port 6000 for single-byte motor commands ('F', 'B', 'L', 'R', 'S')
from the laptop ROS 2 node and writes them directly to the Arduino Uno on /dev/ttyACM0.
"""

import socket
import sys
import time
import serial
import serial.tools.list_ports

PORT_NAME = '/dev/ttyACM0'
BAUD_RATE = 9600
SERVER_PORT = 6000


def get_arduino_serial():
    ports = [p.device for p in serial.tools.list_ports.comports() if 'ttyACM' in p.device or 'ttyUSB' in p.device]
    port = ports[0] if ports else PORT_NAME
    print(f"Connecting to Arduino on {port}...")
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        time.sleep(2)  # Allow Arduino boot
        return ser
    except Exception as e:
        print(f"Serial connection error: {e}")
        return None


def main():
    ser = get_arduino_serial()
    if not ser:
        print("Failed to open Arduino serial. Exiting.")
        sys.exit(1)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', SERVER_PORT))
    server.listen(5)
    print(f"Motor Edge Server listening on 0.0.0.0:{SERVER_PORT}...")

    while True:
        try:
            client, addr = server.accept()
            print(f"Connected by laptop client: {addr}")
            while True:
                data = client.recv(1024)
                if not data:
                    break
                cmd = data.decode('utf-8').strip()
                if cmd and ser and ser.is_open:
                    ser.write(cmd[0].encode('utf-8'))
                    print(f"Relayed to Arduino: {cmd[0]}")
            client.close()
            print("Laptop client disconnected.")
        except Exception as e:
            print(f"Server loop exception: {e}")
            time.sleep(1)


if __name__ == '__main__':
    main()
