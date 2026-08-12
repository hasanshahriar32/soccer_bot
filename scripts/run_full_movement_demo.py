import serial
import time
import sys

def stream_command(ser, left_pwm, right_pwm, duration_sec, name):
    print(f"\n>>> [MOTION] {name}: Left={left_pwm}, Right={right_pwm} for {duration_sec}s...")
    start = time.time()
    packet = f"L:{left_pwm} R:{right_pwm}\n".encode()
    while time.time() - start < duration_sec:
        ser.write(packet)
        ser.flush()
        time.sleep(0.04) # 25 Hz continuous stream to satisfy 500ms watchdog
        if ser.in_waiting:
            ser.read(ser.in_waiting)

def main():
    print("=" * 65)
    print("      SOCCER BOT - FULL 115200 BAUD CONTINUOUS PWM RUNNER")
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

    # Movement Routine
    stream_command(ser, 240, 240, 3.5, "1/4 FORWARD (Full Power)")
    stream_command(ser, 0, 0, 1.0, "PAUSE / STOP")
    stream_command(ser, -220, -220, 2.5, "2/4 BACKWARD")
    stream_command(ser, 0, 0, 1.0, "PAUSE / STOP")
    stream_command(ser, -200, 200, 2.0, "3/4 SPIN LEFT")
    stream_command(ser, 0, 0, 1.0, "PAUSE / STOP")
    stream_command(ser, 200, -200, 2.0, "4/4 SPIN RIGHT")
    stream_command(ser, 0, 0, 1.0, "ALL MOTORS STOPPED")

    ser.close()
    print("\n" + "=" * 65)
    print("     ALL MOVEMENT SEQUENCES COMPLETED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    main()
