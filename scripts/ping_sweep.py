import subprocess
import threading
import socket

active_ips = []

def ping(ip):
    # Quick socket test on common ports
    for port in [22, 5000, 8000, 9000]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            if s.connect_ex((ip, port)) == 0:
                print(f"--> [ACTIVE] {ip} on Port {port}")
                active_ips.append((ip, port))
            s.close()
        except:
            pass

def main():
    print("Sweeping 192.168.0.1 to 192.168.0.254...")
    threads = [threading.Thread(target=ping, args=(f"192.168.0.{i}",)) for i in range(1, 255)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"Sweep complete. Found {len(active_ips)} active ports.")

if __name__ == '__main__':
    main()
