import socket
import threading
import time

def check_ip(ip):
    # Try Port 22 (SSH), Port 5000 (Lidar), Port 8000 (Camera), Port 9000 (Motors)
    for port in [22, 5000, 8000, 9000]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            if s.connect_ex((ip, port)) == 0:
                print(f"[FOUND] Device at {ip} on Port {port}!")
            s.close()
        except:
            pass

def main():
    print("=" * 60)
    print("   DISCOVERING RASPBERRY PI ON LOCAL WI-FI (192.168.0.x)")
    print("=" * 60)
    
    threads = []
    for i in range(1, 255):
        ip = f"192.168.0.{i}"
        t = threading.Thread(target=check_ip, args=(ip,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("=" * 60)

if __name__ == '__main__':
    main()
