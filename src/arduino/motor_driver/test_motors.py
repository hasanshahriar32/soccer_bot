#!/usr/bin/env python3
"""
test_motors.py - Reliable motor test using pyserial.
Keeps the serial port open for the full test so Arduino doesn't reset between commands.
Usage: python3 test_motors.py [port] e.g. python3 test_motors.py /dev/ttyACM0
"""
import sys
import time
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
BAUD = 9600

print("=" * 44)
print(" Soccer Bot Motor Test (Python)")
print(f" Port: {PORT}")
print("=" * 44)

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
except serial.SerialException as e:
    print(f"ERROR: Cannot open {PORT}: {e}")
    sys.exit(1)

# Wait for Arduino to finish resetting after port open
print("\nWaiting for Arduino to boot (2s)...")
time.sleep(2)

def send(cmd, label, duration):
    ser.write(cmd.encode())
    ser.flush()
    response = ser.readline().decode().strip()
    print(f"Sent: {cmd} ({label})  Arduino says: '{response}'")
    time.sleep(duration)

print("\nTesting motors...\n")
send('F', 'Forward',  2)
send('S', 'Stop',     1)
send('B', 'Backward', 2)
send('S', 'Stop',     1)
send('L', 'Left',     1.5)
send('S', 'Stop',     1)
send('R', 'Right',    1.5)
send('S', 'Stop',     0.5)

ser.close()
print("\nMotor test complete. Motors stopped.")
