import socket
import threading
import cv2
import time
from picamera2 import Picamera2

def main():
    print("Initializing Picamera2 on Pi...")
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    print("[SUCCESS] Picamera2 Hardware Initialized!")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 8000))
    server.listen(5)
    print("Camera Server listening on 0.0.0.0:8000...")

    tcp_clients = []
    lock = threading.Lock()

    def accept_thread():
        while True:
            try:
                conn, addr = server.accept()
                with lock:
                    tcp_clients.append(conn)
                print(f"Client connected to Camera from {addr}")
            except:
                pass

    threading.Thread(target=accept_thread, daemon=True).start()

    while True:
        try:
            frame = picam2.capture_array()
            ret, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ret:
                data = buffer.tobytes()
                with lock:
                    dead = []
                    for c in tcp_clients:
                        try:
                            c.sendall(data)
                        except:
                            dead.append(c)
                    for d in dead:
                        tcp_clients.remove(d)
            time.sleep(0.04) # 25 FPS
        except Exception as e:
            time.sleep(0.1)

if __name__ == '__main__':
    main()
