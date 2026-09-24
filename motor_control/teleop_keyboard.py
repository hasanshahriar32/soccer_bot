import socket
import time
import sys

PI_IP = '10.72.30.146'
MOTOR_PORT = 9000

def main():
    print("=" * 60)
    print("       SOCCER BOT - INTERACTIVE KEYBOARD TELEOP")
    print("=" * 60)
    print(f"Connecting to Robot Motor Server at {PI_IP}:{MOTOR_PORT}...")
    
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((PI_IP, MOTOR_PORT))
        print("[SUCCESS] Connected to Soccer Bot Motors!")
    except Exception as e:
        print(f"[ERROR] Could not connect to motor server: {e}")
        return

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
                    sock.sendall(b"F\n")
                elif key == 'S':
                    print(">> [BACKWARD]")
                    sock.sendall(b"B\n")
                elif key == 'A':
                    print(">> [TURN LEFT]")
                    sock.sendall(b"L\n")
                elif key == 'D':
                    print(">> [TURN RIGHT]")
                    sock.sendall(b"R\n")
                elif key in (' ', 'X'):
                    print(">> [STOP]")
                    sock.sendall(b"S\n")
                elif key == 'Q':
                    print(">> Exiting Teleop...")
                    sock.sendall(b"S\n")
                    break
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        if sock:
            sock.sendall(b"S\n")
        print("\nStopping motors...")
    finally:
        if sock:
            try:
                sock.sendall(b"S\n")
                sock.close()
            except:
                pass
        print("Teleop closed safely.")

if __name__ == '__main__':
    main()
