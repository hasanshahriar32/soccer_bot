import serial
import time

def main():
    print("=" * 60)
    print("    TESTING ARDUINO 115200 BAUD PWM STREAM (CONTINUOUS)")
    print("=" * 60)

    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
        time.sleep(2.0)
        print("[OK] Connected to Arduino Uno @ 115200 Baud!")
    except Exception as e:
        print(f"[FAIL] {e}")
        return

    print("\n>>> STREAMING FORWARD COMMANDS (L:220 R:220) AT 20 Hz FOR 5s <<<")
    start_time = time.time()
    count = 0
    while time.time() - start_time < 5.0:
        ser.write(b"L:220 R:220\n")
        ser.flush()
        count += 1
        time.sleep(0.05) # 20 Hz stream
        if ser.in_waiting:
            msg = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
            if msg:
                print(f"Arduino -> {msg}")

    print(f"\nSent {count} PWM packets. Sending STOP (L:0 R:0)...")
    ser.write(b"L:0 R:0\n")
    ser.flush()
    ser.close()
    print("[TEST FINISHED]")
    print("=" * 60)

if __name__ == '__main__':
    main()
