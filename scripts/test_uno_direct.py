import serial
import time
import sys

print("Opening /dev/ttyACM0 @ 9600 baud...")
try:
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1.0)
    time.sleep(2.5) # Wait for Uno reset
    
    # Read boot banner
    boot_msg = ser.read(ser.in_waiting or 100).decode('utf-8', errors='ignore')
    print(f"Boot Banner from Arduino:\n{boot_msg}")
    
    print("\n--- SENDING FORWARD ('F') ---")
    ser.write(b'F\n')
    time.sleep(0.5)
    resp = ser.read(ser.in_waiting or 100).decode('utf-8', errors='ignore')
    print(f"Arduino Response after 'F':\n{resp}")
    
    time.sleep(3.0)
    
    print("\n--- SENDING STOP ('S') ---")
    ser.write(b'S\n')
    time.sleep(0.5)
    resp_stop = ser.read(ser.in_waiting or 100).decode('utf-8', errors='ignore')
    print(f"Arduino Response after 'S':\n{resp_stop}")
    
    ser.close()
    print("\nTest completed!")
except Exception as e:
    print(f"Error: {e}")
