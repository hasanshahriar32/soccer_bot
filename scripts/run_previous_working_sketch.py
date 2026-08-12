import serial
import time
import sys

def main():
    print("=" * 65)
    print("     RUNNING PREVIOUS WORKING MOTOR SKETCH ROUTINE")
    print("=" * 65)

    port = '/dev/ttyACM0'
    baud = 9600

    try:
        ser = serial.Serial(port, baud, timeout=1.0)
        time.sleep(2.0)
        print(f"[OK] Connected to Arduino on {port} @ {baud} Baud!")
    except Exception as e:
        print(f"[FAIL] Could not open {port}: {e}")
        return

    routine = [
        ('F', 'FORWARD', 3.0),
        ('S', 'STOP', 1.0),
        ('B', 'BACKWARD', 3.0),
        ('S', 'STOP', 1.0),
        ('L', 'TURN LEFT', 2.0),
        ('S', 'STOP', 1.0),
        ('R', 'TURN RIGHT', 2.0),
        ('S', 'FINAL STOP', 0.5)
    ]

    for cmd, desc, duration in routine:
        print(f"\n>>> Executing [{cmd}] - {desc} for {duration}s...")
        ser.write(cmd.encode())
        ser.flush()
        time.sleep(duration)
        if ser.in_waiting:
            reply = ser.read(ser.in_waiting).decode('utf-8', errors='ignore').strip()
            print(f"Arduino -> {reply}")

    ser.close()
    print("\n" + "=" * 65)
    print("       PREVIOUS MOTOR TEST COMPLETED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    main()
