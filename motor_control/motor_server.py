import socket
import serial
import threading
import time
import sys

print("[1] Opening /dev/ttyACM0 @ 9600 baud...", flush=True)
try:
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0.1)
    time.sleep(2.0)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print("[2] Arduino Serial ready!", flush=True)
except Exception as e:
    print(f"[ERROR] Could not open /dev/ttyACM0: {e}", flush=True)
    sys.exit(1)

lock = threading.Lock()

def handle_client(conn, addr):
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"[CLIENT CONNECTED] {addr}", flush=True)
    try:
        while True:
            data = conn.recv(64)
            if not data:
                break
            text = data.decode('utf-8', errors='ignore')
            for ch in text:
                if ch in 'FBLRS':
                    with lock:
                        ser.write(ch.encode('utf-8'))
                        ser.flush()
                    print(f"[ACTION] Executed '{ch}' for {addr}", flush=True)
    except Exception as e:
        print(f"[CLIENT ERR] {e}", flush=True)
    finally:
        conn.close()
        print(f"[CLIENT DISCONNECTED] {addr}", flush=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
server.bind(('0.0.0.0', 9000))
server.listen(10)
print("[3] Multi-threaded Motor Server listening on 0.0.0.0:9000...", flush=True)

while True:
    try:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as err:
        print(f"[SERVER ERR] {err}", flush=True)
        time.sleep(0.5)
