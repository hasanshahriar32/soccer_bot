import socket
import threading

def check_ip(ip, results):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.35)
        res = s.connect_ex((ip, 22))
        if res == 0:
            results.append(ip)
        s.close()
    except:
        pass

def main():
    print("Scanning current Wi-Fi subnet 10.61.32.x for active SSH (Port 22)...")
    results = []
    threads = []
    
    for i in range(1, 255):
        ip = f"10.61.32.{i}"
        t = threading.Thread(target=check_ip, args=(ip, results))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("\nScan complete. Active SSH Hosts found on 10.61.32.x:")
    for ip in results:
        print(f"-> {ip}")

    # Also try resolving mDNS hostnames
    for name in ['pihole.local', 'raspberrypi.local', 'pi.local', 'soccerbot.local']:
        try:
            resolved = socket.gethostbyname(name)
            print(f"-> mDNS resolved {name} = {resolved}")
        except Exception:
            pass

if __name__ == '__main__':
    main()
