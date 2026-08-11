import serial
import time
import sys

def main():
    print("=" * 65)
    print("      ARDUINO & MOTOR DRIVER LIVE HARDWARE AUDIT")
    print("=" * 65)

    port = '/dev/ttyACM0'
    baud = 9600

    print(f"[1] Connecting to Arduino on {port} @ {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=2.0)
        time.sleep(2.5) # Wait for Uno DTR reset
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("[OK] Arduino Serial port opened successfully!\n")
    except Exception as e:
        print(f"[FAIL] Could not open {port}: {e}")
        return

    # Test Commands Matrix
    tests = [
        ('F', 'FORWARD (Left & Right Wheels Drive Forward)', 3.0),
        ('S', 'STOP (All Wheels Halted)', 1.0),
        ('B', 'BACKWARD (Left & Right Wheels Drive Backward)', 3.0),
        ('S', 'STOP (All Wheels Halted)', 1.0),
        ('L', 'TURN LEFT (Left Wheels Backward, Right Wheels Forward)', 3.0),
        ('S', 'STOP (All Wheels Halted)', 1.0),
        ('R', 'TURN RIGHT (Left Wheels Forward, Right Wheels Backward)', 3.0),
        ('S', 'STOP (All Wheels Halted)', 1.0)
    ]

    print("[2] Executing Hardware Motor Pin Command Sequence:\n")
    for cmd, desc, duration in tests:
        print(f"  -> Sending Command: '{cmd}' [{desc}]...")
        ser.write(cmd.encode('utf-8') + b'\n')
        ser.flush()
        
        time.sleep(0.3)
        resp = ser.read(ser.in_waiting or 64).decode('utf-8', errors='ignore').strip()
        print(f"     Arduino Feedback: '{resp}'")
        
        time.sleep(duration)

    ser.close()
    print("\n" + "=" * 65)
    print(">>> ARDUINO HARDWARE TEST COMPLETE <<<")
    print("=" * 65)

if __name__ == '__main__':
    main()
