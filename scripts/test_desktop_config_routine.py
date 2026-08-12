import serial
import time
import sys

def stream_step(ser, left_pwm, right_pwm, duration_sec, step_name):
    print(f"\n>>> [{step_name}] PWM: Left={left_pwm}, Right={right_pwm} for {duration_sec}s...")
    start = time.time()
    packet = f"L:{left_pwm} R:{right_pwm}\n".encode()
    while time.time() - start < duration_sec:
        ser.write(packet)
        ser.flush()
        time.sleep(0.04) # 25 Hz stream to satisfy watchdog
        if ser.in_waiting:
            ser.read(ser.in_waiting)

def main():
    print("=" * 65)
    print("   SOCCER BOT - DESKTOP CONFIGURATION MOVEMENT TEST")
    print("=" * 65)

    port = '/dev/ttyACM0'
    baud = 115200

    try:
        ser = serial.Serial(port, baud, timeout=0.5)
        time.sleep(2.0)
        print(f"[OK] Connected to Arduino Uno on {port} @ {baud} Baud!")
    except Exception as e:
        print(f"[FAIL] Could not open {port}: {e}")
        return

    # 1. Forward
    stream_step(ser, 240, 240, 3.0, "1/4 FORWARD (Both Wheels)")
    stream_step(ser, 0, 0, 1.0, "PAUSE / STOP")

    # 2. Backward
    stream_step(ser, -240, -240, 2.5, "2/4 BACKWARD (Both Wheels)")
    stream_step(ser, 0, 0, 1.0, "PAUSE / STOP")

    # 3. Left Turn
    stream_step(ser, -200, 200, 2.0, "3/4 LEFT TURN")
    stream_step(ser, 0, 0, 1.0, "PAUSE / STOP")

    # 4. Right Turn
    stream_step(ser, 200, -200, 2.0, "4/4 RIGHT TURN")
    stream_step(ser, 0, 0, 0.5, "ALL MOTORS STOPPED")

    ser.close()
    print("\n" + "=" * 65)
    print("     TEST COMPLETED PER DESKTOP CONFIGURATION!")
    print("=" * 65)

if __name__ == '__main__':
    main()
