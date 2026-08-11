import paramiko
import time
import sys
import threading

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("       SOCCER BOT - INTERACTIVE KEYBOARD TELEOP")
    print("=" * 60)
    print("Connecting to Raspberry Pi & Arduino (/dev/ttyACM0)...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
        print("[SUCCESS] Connected to Robot!")
    except Exception as e:
        print(f"[ERROR] Could not connect to Pi: {e}")
        return

    # Deploy remote driver session
    channel = ssh.invoke_shell()
    channel.send("python3 -u -c \"import serial, sys; s = serial.Serial('/dev/ttyACM0', 9600, timeout=1); print('READY'); sys.stdout.flush(); [s.write(c.encode()) for c in iter(lambda: sys.stdin.read(1), '')]\"\n")
    time.sleep(1.5)

    print("\n" + "-" * 60)
    print("  CONTROL KEYS:")
    print("    [ W ] -> Forward")
    print("    [ S ] -> Backward")
    print("    [ A ] -> Turn Left")
    print("    [ D ] -> Turn Right")
    print("    [ SPACE / X ] -> STOP")
    print("    [ Q ] -> Quit Teleop")
    print("-" * 60 + "\n")

    try:
        import msvcrt # Windows native instant keypress without Enter
        
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8', errors='ignore').upper()
                
                if key == 'W':
                    print(">> [FORWARD]")
                    channel.send("F")
                elif key == 'S':
                    print(">> [BACKWARD]")
                    channel.send("B")
                elif key == 'A':
                    print(">> [TURN LEFT]")
                    channel.send("L")
                elif key == 'D':
                    print(">> [TURN RIGHT]")
                    channel.send("R")
                elif key in (' ', 'X'):
                    print(">> [STOP]")
                    channel.send("S")
                elif key == 'Q':
                    print(">> Exiting Teleop...")
                    channel.send("S")
                    break
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        channel.send("S")
        print("\nStopping motors...")
    finally:
        channel.send("S")
        channel.close()
        ssh.close()
        print("Teleop closed safely.")

if __name__ == '__main__':
    main()
