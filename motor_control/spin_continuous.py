import paramiko
import time
import argparse
import sys

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    parser = argparse.ArgumentParser(description="Continuous Motor Spinner")
    parser.add_argument('--dir', type=str, default='F', choices=['F', 'B', 'L', 'R'], help="Direction: F=Forward, B=Backward, L=Left, R=Right")
    parser.add_argument('--duration', type=float, default=0, help="Duration in seconds (0 = infinite until Ctrl+C)")
    args = parser.parse_args()

    dir_names = {'F': 'FORWARD', 'B': 'BACKWARD', 'L': 'LEFT SPIN (CCW)', 'R': 'RIGHT SPIN (CW)'}
    mode_name = dir_names.get(args.dir.upper(), 'FORWARD')
    
    print("=" * 60)
    print(f"      SOCCER BOT - CONTINUOUS {mode_name}")
    print("=" * 60)
    print(f"Connecting to Raspberry Pi ({PI_IP})...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
    
    channel = ssh.invoke_shell()
    channel.send("python3 -u -c \"import serial, sys; s = serial.Serial('/dev/ttyACM0', 9600, timeout=1); print('READY'); sys.stdout.flush(); [s.write(c.encode()) for c in iter(lambda: sys.stdin.read(1), '')]\"\n")
    time.sleep(1.5)

    print(f"\n>>> Motors ENGAGED: {mode_name} (Command: '{args.dir}') <<<")
    if args.duration > 0:
        print(f">>> Running for {args.duration} seconds...")
    else:
        print(">>> Running continuously. Press [Ctrl+C] to STOP! <<<")

    channel.send(args.dir.upper())

    try:
        if args.duration > 0:
            time.sleep(args.duration)
        else:
            while True:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nInterrupt received!")
    finally:
        print("\nStopping motors safely...")
        channel.send("S")
        time.sleep(0.5)
        channel.send("S")
        channel.close()
        ssh.close()
        print("Motors stopped successfully.")

if __name__ == '__main__':
    main()
