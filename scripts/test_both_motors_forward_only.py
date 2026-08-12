import serial
import time
import sys

def main():
    print("=" * 65)
    print("      SOCCER BOT - FORWARD ONLY (BOTH MOTORS FULL POWER)")
    print("=" * 65)

    port = '/dev/ttyACM0'
    baud = 115200

    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        time.sleep(2.0)
        print(f"[OK] Connected to Arduino Uno on {port} @ {baud} Baud!")
    except Exception as e:
        print(f"[FAIL] {e}")
        return

    print("\n>>> SPINNING BOTH MOTORS FORWARD AT 100% POWER (6 Seconds)...")
    print("--> Left Motor:  IN1=HIGH (D9),  IN2=LOW (D10), ENA=255 (D5)")
    print("--> Right Motor: IN3=LOW (D11),  IN4=HIGH (D12), ENB=255 (D6)")
    print("-" * 65)

    start = time.time()
    while time.time() - start < 6.0:
        ser.write(b"L:255 R:255\n")
        ser.write(b"F\n")
        ser.flush()
        time.sleep(0.04) # 25Hz continuous keepalive

    # Stop
    ser.write(b"L:0 R:0\n")
    ser.write(b"S\n")
    ser.flush()
    ser.close()

    print("\n[SUCCESS] 6-SECOND FORWARD TEST COMPLETED!")
    print("=" * 65)

if __name__ == '__main__':
    main()
