import serial
import time

def main():
    print("=" * 60)
    print("      ALL-PINS HIGH TEST (PWM 100% MAXIMUM POWER)")
    print("=" * 60)

    try:
        ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1.0)
        time.sleep(2.0)
        print("[OK] Connected to Arduino Uno on /dev/ttyACM0")
    except Exception as e:
        print(f"[FAIL] Could not connect to Arduino: {e}")
        return

    # Send 'F' repeatedly for 8 seconds
    print("\n>>> PUMPING CONTINUOUS FORWARD VOLTAGE INTO ARDUINO <<<")
    for i in range(1, 9):
        ser.write(b'F\n')
        ser.flush()
        time.sleep(0.3)
        resp = ser.read(ser.in_waiting or 64).decode('utf-8', errors='ignore').strip()
        print(f"[{i}/8] Arduino Status: {resp}")
        time.sleep(0.7)

    ser.write(b'S\n')
    ser.flush()
    ser.close()
    print("\n[TEST COMPLETED]")
    print("=" * 60)

if __name__ == '__main__':
    main()
