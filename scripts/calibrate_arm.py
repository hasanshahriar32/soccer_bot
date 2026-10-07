#!/usr/bin/env python3
"""
====================================================================
  SOCCER BOT - 4-DOF ROBOTIC ARM CALIBRATION & TEST UTILITY
====================================================================
Usage:
  python3 scripts/calibrate_arm.py                # Interactive menu
  python3 scripts/calibrate_arm.py --auto         # Full automated calibration
  python3 scripts/calibrate_arm.py --gripper      # Gripper range test
  python3 scripts/calibrate_arm.py --base         # Base rotation test
  python3 scripts/calibrate_arm.py --pickup       # Automated ball pickup test
====================================================================
"""

import sys
import time
import socket
import json
import argparse

def discover_pi_ip():
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        return sys.argv[1]
    candidates = ["192.168.0.135", "10.127.69.146", "10.61.32.146", "10.72.30.146"]
    for ip in candidates:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.25)
            if s.connect_ex((ip, 22)) == 0 or s.connect_ex((ip, 9001)) == 0:
                s.close()
                return ip
            s.close()
        except Exception:
            pass
    return "192.168.0.135"

PI_IP = discover_pi_ip()
PI_ARM_PORT = 9001

class ArmClient:
    def __init__(self, host=PI_IP, port=PI_ARM_PORT):
        self.host = host
        self.port = port

    def send(self, cmd_dict, timeout=20.0):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(timeout)
            sock.connect((self.host, self.port))
            payload = json.dumps(cmd_dict) + "\n"
            sock.sendall(payload.encode('utf-8'))
            data = sock.recv(2048).decode('utf-8').strip()
            sock.close()
            return json.loads(data)
        except Exception as e:
            return {"status": "ERR", "msg": str(e), "connected": False}

    def get_status(self):
        return self.send({"action": "status"})

    def set_joint(self, joint, angle):
        return self.send({"action": "joint", "joint": joint.upper(), "angle": int(angle)})

    def home(self):
        return self.send({"action": "home"})

    def ready(self):
        return self.send({"action": "ready"})

    def pickup(self):
        return self.send({"action": "pickup"}, timeout=25.0)

    def test(self):
        return self.send({"action": "test"}, timeout=30.0)

def print_status_bar(st):
    b = st.get('base', '?')
    s = st.get('shoulder', '?')
    a = st.get('albo', '?')
    g = st.get('gripper', '?')
    conn = "ONLINE" if st.get('connected') else "OFFLINE"
    print(f"\033[1;36m[STATE]\033[0m Link: {conn} | Base: {b}° | Shoulder: {s}° | Elbow: {a}° | Gripper: {g}°")

def run_gripper_test(client):
    print("\n\033[1;33m--- Testing Gripper Calibration (Pin 12: 90° Clamp -> 270° Open) ---\033[0m")
    steps = [
        (90,  "Full Clamp (Closed / Hold Ball)"),
        (135, "Tight Hold"),
        (180, "Neutral / Half Open"),
        (225, "Wide Open"),
        (270, "Maximum Reach Open"),
        (180, "Return to Neutral"),
        (90,  "Return to Closed / Parked"),
    ]
    for angle, label in steps:
        t0 = time.time()
        print(f"  → Setting Gripper to {angle:3d}° ({label})...", end="", flush=True)
        res = client.set_joint('G', angle)
        dt = time.time() - t0
        status = "\033[1;32mOK\033[0m" if res.get('status') == 'OK' else f"\033[1;31m{res.get('msg')}\033[0m"
        print(f" {status} ({dt:.2f}s) -> ACK: {res.get('response', '')}")
        time.sleep(0.8)

def run_base_test(client):
    print("\n\033[1;33m--- Testing Base Servo Calibration (Pin 9: 0° Right -> 180° Left) ---\033[0m")
    steps = [
        (90,  "Center / Forward Facing"),
        (45,  "Turn Right 45°"),
        (0,   "Turn Hard Right 0°"),
        (45,  "Return to Right 45°"),
        (90,  "Center 90°"),
        (135, "Turn Left 135°"),
        (180, "Turn Hard Left 180°"),
        (90,  "Return to Center 90°"),
    ]
    for angle, label in steps:
        t0 = time.time()
        print(f"  → Setting Base to {angle:3d}° ({label})...", end="", flush=True)
        res = client.set_joint('B', angle)
        dt = time.time() - t0
        status = "\033[1;32mOK\033[0m" if res.get('status') == 'OK' else f"\033[1;31m{res.get('msg')}\033[0m"
        print(f" {status} ({dt:.2f}s) -> ACK: {res.get('response', '')}")
        time.sleep(1.0)

def run_arm_coordination_test(client):
    print("\n\033[1;33m--- Testing Shoulder & Elbow Articulation ---\033[0m")
    poses = [
        (30, 20, "Low Reach"),
        (60, 50, "Forward Reach"),
        (70, 80, "Ground Pickup Ready"),
        (0,  0,  "Rest / Folded"),
    ]
    for s, a, label in poses:
        print(f"  → Moving to {label} (Shoulder: {s}°, Elbow: {a}°)...")
        res_s = client.set_joint('S', s)
        time.sleep(0.2)
        res_a = client.set_joint('A', a)
        time.sleep(1.2)
        print_status_bar(client.get_status())

def run_full_calibration(client):
    print("\n\033[1;32m======================================================")
    print("      SOCCER BOT ROBOTIC HAND FULL CALIBRATION")
    print(f"      Target: {client.host}:{client.port}")
    print("======================================================\033[0m")
    
    st = client.get_status()
    print_status_bar(st)
    if not st.get('connected'):
        print("\033[1;31m[ERROR] Robotic Arm server not connected to Arduino.\033[0m")
        return

    # 1. Gripper Calibration
    run_gripper_test(client)

    # 2. Base Sweep Calibration
    run_base_test(client)

    # 3. Shoulder / Elbow Coordination
    run_arm_coordination_test(client)

    # 4. Preset Verification
    print("\n\033[1;33m--- Verifying Presets ---\033[0m")
    print("  → Testing READY Pose...")
    r = client.ready()
    print(f"    ACK: {r.get('response')} | Base: {r.get('base')}° Shoulder: {r.get('shoulder')}° Elbow: {r.get('albo')}° Gripper: {r.get('gripper')}°")
    time.sleep(2.0)

    print("  → Testing HOME Pose...")
    h = client.home()
    print(f"    ACK: {h.get('response')} | Base: {h.get('base')}° Shoulder: {h.get('shoulder')}° Elbow: {h.get('albo')}° Gripper: {h.get('gripper')}°")
    time.sleep(2.0)

    print("\n\033[1;32m✅ Calibration & Motion Verification Complete!\033[0m\n")
    print_status_bar(client.get_status())

def main():
    parser = argparse.ArgumentParser(description="Soccer Bot Hand Calibration Utility")
    parser.add_argument("--auto", action="store_true", help="Run full automated calibration")
    parser.add_argument("--gripper", action="store_true", help="Run gripper sweep test")
    parser.add_argument("--base", action="store_true", help="Run base rotation sweep test")
    parser.add_argument("--pickup", action="store_true", help="Run automated ball pickup routine")
    parser.add_argument("--host", default=PI_IP, help=f"Pi IP address (default: {PI_IP})")
    args = parser.parse_args()

    client = ArmClient(host=args.host)

    if args.auto:
        run_full_calibration(client)
        return
    elif args.gripper:
        run_gripper_test(client)
        return
    elif args.base:
        run_base_test(client)
        return
    elif args.pickup:
        print("\n\033[1;33m--- Executing Automated Ball Pickup Routine ---\033[0m")
        res = client.pickup()
        print("Pickup finished:", res)
        return

    # Interactive Menu
    while True:
        print("\n\033[1;36m====================================================")
        print("       SOCCER BOT HAND CALIBRATION & TEST")
        print("====================================================\033[0m")
        st = client.get_status()
        print_status_bar(st)
        print(" 1) Run Full Automated Calibration Sweep")
        print(" 2) Test Gripper Range (90° Clamp -> 270° Open)")
        print(" 3) Test Base Range (0° Right -> 180° Left)")
        print(" 4) Test Shoulder & Elbow Coordination")
        print(" 5) Test Automated Ball Pickup Routine")
        print(" 6) Move Joint (Manual Angle Entry)")
        print(" 7) Set HOME Pose (B:0 S:0 A:0 G:90)")
        print(" 8) Set READY Pose (B:90 S:70 A:80 G:240)")
        print(" Q) Quit")
        choice = input("\nEnter choice [1-8, Q]: ").strip().upper()

        if choice == '1':
            run_full_calibration(client)
        elif choice == '2':
            run_gripper_test(client)
        elif choice == '3':
            run_base_test(client)
        elif choice == '4':
            run_arm_coordination_test(client)
        elif choice == '5':
            print("\nExecuting Pickup Routine...")
            r = client.pickup()
            print("Result:", r)
        elif choice == '6':
            j = input("Enter Joint [B=Base, S=Shoulder, A=Elbow, G=Gripper]: ").strip().upper()
            if j in ['B', 'S', 'A', 'G']:
                try:
                    ang = int(input(f"Enter target angle for {j}: ").strip())
                    res = client.set_joint(j, ang)
                    print("ACK:", res)
                except ValueError:
                    print("Invalid angle integer.")
            else:
                print("Unknown joint code.")
        elif choice == '7':
            print(client.home())
        elif choice == '8':
            print(client.ready())
        elif choice in ('Q', 'EXIT'):
            print("Exiting calibration utility.")
            break
        else:
            print("Invalid choice, try again.")

if __name__ == '__main__':
    main()
