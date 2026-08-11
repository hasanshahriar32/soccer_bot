import serial
import time
import sys

def main():
    print("=" * 60)
    print("    CONTINUOUS MOTOR POWER TEST (FULL 100% TORQUE)")
    print("=" * 60)

    try:
        ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1.0)
        time.sleep(2.0)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("[OK] Serial Connected to Arduino Uno on /dev/ttyACM0!")
    except Exception as e:
        print(f"[FAIL] Could not open /dev/ttyACM0: {e}")
        return

    print("\n>>> SENDING CONTINUOUS FORWARD ('F') COMMAND <<<")
    print("Keep your eyes on the robot wheels!")
    
    for i in range(1, 11):
        ser.write(b'F\n')
        ser.flush()
        time.sleep(0.2)
        resp = ser.read(ser.in_waiting or 32).decode('utf-8', errors='ignore').strip()
        print(f"[{i}/10] Sent 'F' -> Arduino reply: '{resp}'")
        time.sleep(0.8)

    print("\nSending STOP ('S')...")
    ser.write(b'S\n')
    ser.flush()
    ser.close()
    print("[TEST FINISHED]")
    print("=" * 60)

if __name__ == '__main__':
    main()
