import socket
import threading
import sys

def check_ip(ip, results):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        res = s.connect_ex((ip, 22))
        if res == 0:
            results.append(ip)
        s.close()
    except:
        pass

def main():
    print("Scanning subnet 192.168.0.x for active SSH (Port 22)...")
    results = []
    threads = []
    
    for i in range(1, 255):
        ip = f"192.168.0.{i}"
        t = threading.Thread(target=check_ip, args=(ip, results))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("\nScan complete. Active SSH Hosts found:")
    for ip in results:
        print(f"-> {ip}")

if __name__ == '__main__':
    main()
