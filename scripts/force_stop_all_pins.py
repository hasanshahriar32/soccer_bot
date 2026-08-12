import serial
import time

def main():
    print("=" * 60)
    print("       FORCE STOP ALL MOTOR PINS (LOCK TO 0V LOW)")
    print("=" * 60)

    try:
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1.0)
        time.sleep(2.0)
        print("[OK] Serial Connected to Arduino Uno!")
    except Exception as e:
        print(f"[FAIL] {e}")
        return

    # Send explicit Stop to clear all pins to 0V
    ser.write(b"L:0 R:0\n")
    ser.write(b"S\n")
    ser.flush()
    time.sleep(0.5)

    if ser.in_waiting:
        print("Arduino Response:", ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip())

    ser.close()
    print("[SUCCESS] All Arduino pins (D9, D10, D11, D12) locked to LOW (0V).")
    print("=" * 60)

if __name__ == '__main__':
    main()
