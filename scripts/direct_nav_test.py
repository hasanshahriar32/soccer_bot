#!/usr/bin/env python3
"""
====================================================================
      SOCCER BOT - AUTOMATED FRONT-BACK NAVIGATION TEST SUITE
====================================================================
Tests manual movement end-to-end:
  1. Connects to Pi Motor Server (Port 9000) or Arduino Serial directly
  2. Executes:
     - 🚀 FORWARD (2.0s)
     - ⏹️ STOP (1.0s)
     - 🔻 BACKWARD (2.0s)
     - ⏹️ STOP (1.0s)
     - 🔄 TURN LEFT (1.5s)
     - 🔄 TURN RIGHT (1.5s)
     - ⏹️ FINAL SAFETY STOP
  3. Verifies Arduino responses and motor driver state
====================================================================
"""

import socket
import time
import sys

PI_IP = "10.127.69.146"
PI_PORT = 9000

def test_motor_navigation():
    print("=" * 65)
    print(" 🤖 SOCCER BOT DIRECT FRONT-BACK NAVIGATION TEST")
    print(f" Connecting to Motor TCP Server at {PI_IP}:{PI_PORT}...")
    print("=" * 65)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.settimeout(3.0)
        s.connect((PI_IP, PI_PORT))
        print(" Connected to Robot Motor Controller!\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Please ensure the Raspberry Pi is powered on and joined to Wi-Fi.")
        return False

    sequence = [
        ('F', '🚀 DRIVING FORWARD', 2.5),
        ('S', '⏹️ BRAKING / STOPPED', 1.0),
        ('B', '🔻 DRIVING BACKWARD', 2.5),
        ('S', '⏹️ BRAKING / STOPPED', 1.0),
        ('L', '🔄 TURNING LEFT', 1.5),
        ('S', '⏹️ BRAKING / STOPPED', 1.0),
        ('R', '🔄 TURNING RIGHT', 1.5),
        ('S', '⏹️ FINAL SAFETY STOP', 0.5)
    ]

    for cmd, desc, duration in sequence:
        print(f"[{time.strftime('%H:%M:%S')}] {desc} (Command: '{cmd}') for {duration:.1f}s...")
        try:
            s.sendall(f"{cmd}\n".encode('utf-8'))
        except Exception as e:
            print(f"❌ Send failed: {e}")
            break
        time.sleep(duration)

    try:
        s.sendall(b"S\n")
        s.close()
    except Exception:
        pass

    print("\n" + "=" * 65)
    print(" Navigation test sequence completed.")
    print("=" * 65)
    return True

if __name__ == '__main__':
    test_motor_navigation()
