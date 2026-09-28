import paramiko
import time
import sys

PI_IP = '192.168.0.135'
PI_USER = 'hasan'
PI_PASS = 'grammarpro'

def main():
    print("=" * 60)
    print("       SOCCER BOT - CONTINUOUS MOTOR SPIN CONTROLLER")
    print("=" * 60)
    
    print("\nSelect Continuous Spin Mode:")
    print("  [1] Continuous FORWARD (Drive Straight)")
    print("  [2] Continuous LEFT Spin (Rotate Counter-Clockwise)")
    print("  [3] Continuous RIGHT Spin (Rotate Clockwise)")
    print("  [4] Continuous BACKWARD (Reverse)")
    
    choice = input("\nEnter choice [1/2/3/4] (Default: 1): ").strip()
    cmd_map = {'1': ('F', 'FORWARD'), '2': ('L', 'LEFT SPIN'), '3': ('R', 'RIGHT SPIN'), '4': ('B', 'BACKWARD')}
    cmd, mode_name = cmd_map.get(choice, ('F', 'FORWARD'))
    
    print(f"\nConnecting to Robot at {PI_IP}...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASS, timeout=8)
        print("[SUCCESS] Connected!")
    except Exception as e:
        print(f"[ERROR] SSH failed: {e}")
        return

    # Start interactive shell channel
    channel = ssh.invoke_shell()
    channel.send("python3 -u -c \"import serial, sys; s = serial.Serial('/dev/ttyACM0', 9600, timeout=1); print('READY'); sys.stdout.flush(); [s.write(c.encode()) for c in iter(lambda: sys.stdin.read(1), '')]\"\n")
    time.sleep(1.5)

    print("\n" + "=" * 60)
    print(f"  >>> MOTOR SPINNING: {mode_name} (Command: '{cmd}') <<<")
    print("  >>> Press [ENTER] or [Ctrl+C] at any time to STOP! <<<")
    print("=" * 60 + "\n")

    # Send continuous run command
    channel.send(cmd)

    try:
        # Keep alive until user input
        input("Motors are currently spinning... Press [ENTER] to STOP: ")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\n[STOPPING MOTORS] Sending 'S' safe stop command...")
        channel.send("S")
        time.sleep(0.5)
        channel.send("S")
        channel.close()
        ssh.close()
        print("[DONE] Motors safely stopped.")

if __name__ == '__main__':
    main()
