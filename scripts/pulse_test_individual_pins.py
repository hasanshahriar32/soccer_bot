import serial
import time
import socket

def main():
    print("=" * 60)
    print("     DIAGNOSTIC TEST: INDIVIDUAL MOTOR PULSES")
    print("=" * 60)

    PI_IP = '192.168.0.135'
    
    commands = [
        ('F', 'FORWARD (Both Motors 100% Torque)', 3.0),
        ('S', 'STOPPING', 1.0),
        ('L', 'SPIN LEFT (Left Back, Right Forward)', 2.5),
        ('S', 'STOPPING', 1.0),
        ('R', 'SPIN RIGHT (Left Forward, Right Back)', 2.5),
        ('S', 'ALL MOTORS STOPPED', 0.5),
    ]

    for cmd, desc, duration in commands:
        print(f"\n>>> Executing [{cmd}]: {desc} for {duration}s...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.settimeout(2.0)
            s.connect((PI_IP, 9000))
            s.sendall(cmd.encode())
            s.close()
        except Exception as e:
            print(f"Error sending command: {e}")
        time.sleep(duration)

    print("\n" + "=" * 60)
    print("DIAGNOSTIC PULSE SEQUENCE FINISHED")
    print("=" * 60)

if __name__ == '__main__':
    main()
