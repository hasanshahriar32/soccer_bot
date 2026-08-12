import serial
import time
import sys

def main():
    print("=" * 65)
    print("      DIRECT LEFT MOTOR CONTINUOUS POWER STREAM")
    print("=" * 65)

    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
        time.sleep(2.0)
        print("[OK] Connected to Arduino Uno on /dev/ttyACM0 @ 115200 Baud!")
    except Exception as e:
        print(f"[FAIL] {e}")
        return

    # Flush buffers
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    print("\n>>> PUMPING 100% MAXIMUM POWER TO LEFT MOTOR (6 Seconds)...")
    print("--> Pins Triggered: D9=HIGH, D10=LOW, ENA=HIGH (D5)")
    print("-" * 65)

    start = time.time()
    while time.time() - start < 6.0:
        ser.write(b"L:255 R:0\n")
        ser.flush()
        time.sleep(0.04)
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"[Arduino Echo] {line}")

    # Stop
    ser.write(b"L:0 R:0\n")
    ser.write(b"S\n")
    ser.flush()
    ser.close()

    print("\n[SUCCESS] Direct test completed!")
    print("=" * 65)

if __name__ == '__main__':
    main()
