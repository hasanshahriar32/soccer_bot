import serial
import time

def main():
    print("=" * 60)
    print("       DIAGNOSTIC: ALL DIGITAL PINS HIGH (5V POWER)")
    print("=" * 60)

    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
        time.sleep(2.0)
        print("[OK] Connected to Arduino Uno!")
    except Exception as e:
        print(f"[FAIL] {e}")
        return

    # Send maximum forward torque continuously
    print("\n>>> PUMPING MAXIMUM VOLTAGE TO ALL OUTPUTS (5 SECONDS) <<<")
    start = time.time()
    while time.time() - start < 5.0:
        ser.write(b"L:255 R:255\n")
        ser.write(b"F\n")
        ser.flush()
        time.sleep(0.05)

    ser.write(b"L:0 R:0\n")
    ser.write(b"S\n")
    ser.flush()
    ser.close()
    print("[TEST COMPLETED]")
    print("=" * 60)

if __name__ == '__main__':
    main()
