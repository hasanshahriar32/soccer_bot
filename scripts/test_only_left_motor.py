import serial
import time
import sys

def main():
    print("=" * 65)
    print("        TESTING ONLY LEFT MOTOR (OUT1 / OUT2 / D9 / D10)")
    print("=" * 65)

    port = '/dev/ttyACM0'
    baud = 115200

    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        time.sleep(2.0)
        print(f"[OK] Connected to Arduino on {port} @ {baud} Baud!")
    except Exception as e:
        print(f"[FAIL] {e}")
        return

    # 1. Left Motor Forward (6 Seconds)
    print("\n>>> [1/2] SPINNING LEFT MOTOR FORWARD (6 Seconds)...")
    start = time.time()
    while time.time() - start < 6.0:
        ser.write(b"L:255 R:0\n")
        ser.write(b"F\n")
        ser.flush()
        time.sleep(0.04)

    # Pause
    ser.write(b"L:0 R:0\n")
    ser.write(b"S\n")
    ser.flush()
    time.sleep(1.0)

    # 2. Left Motor Backward (4 Seconds)
    print(">>> [2/2] SPINNING LEFT MOTOR REVERSE (4 Seconds)...")
    start = time.time()
    while time.time() - start < 4.0:
        ser.write(b"L:-255 R:0\n")
        ser.write(b"B\n")
        ser.flush()
        time.sleep(0.04)

    # Stop
    ser.write(b"L:0 R:0\n")
    ser.write(b"S\n")
    ser.flush()
    ser.close()
    print("\n[LEFT MOTOR TEST COMPLETED]")
    print("=" * 65)

if __name__ == '__main__':
    main()
