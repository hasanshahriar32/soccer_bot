import serial
import time
import sys

def main():
    print("=" * 65)
    print("      STRICT LEFT MOTOR ONLY TEST (RIGHT MOTOR 100% OFF)")
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

    # Explicitly lock Right Motor to 0
    # 1. Left Motor Forward ONLY (5 Seconds)
    print("\n>>> [1/2] SPINNING ONLY LEFT MOTOR FORWARD (5 Seconds)...")
    print("--> Left Motor:  PWM = 255 (Pins D9=HIGH, D10=LOW)")
    print("--> Right Motor: PWM = 0   (Pins D11=LOW,  D12=LOW - LOCKED OFF)")
    print("-" * 65)
    
    start = time.time()
    while time.time() - start < 5.0:
        ser.write(b"L:255 R:0\n")
        ser.flush()
        time.sleep(0.04)

    # Pause / Stop
    ser.write(b"L:0 R:0\n")
    ser.flush()
    time.sleep(1.5)

    # 2. Left Motor Reverse ONLY (4 Seconds)
    print(">>> [2/2] SPINNING ONLY LEFT MOTOR REVERSE (4 Seconds)...")
    print("--> Left Motor:  PWM = -255 (Pins D9=LOW,  D10=HIGH)")
    print("--> Right Motor: PWM = 0    (Pins D11=LOW, D12=LOW - LOCKED OFF)")
    print("-" * 65)
    
    start = time.time()
    while time.time() - start < 4.0:
        ser.write(b"L:-255 R:0\n")
        ser.flush()
        time.sleep(0.04)

    # Final Stop
    ser.write(b"L:0 R:0\n")
    ser.flush()
    ser.close()

    print("\n[SUCCESS] STRICT LEFT MOTOR ONLY TEST COMPLETED!")
    print("=" * 65)

if __name__ == '__main__':
    main()
