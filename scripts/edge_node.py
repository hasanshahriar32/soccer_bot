import cv2
import socket
import struct
import time

def stream_camera():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 15)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 5001))
    server_socket.listen(1)
    print("Camera server listening on port 5001...")
    
    while True:
        client_socket, addr = server_socket.accept()
        print('Connection from:', addr)
        try:
            while True:
                ret, frame = cap.read()
                if not ret: continue
                result, encoded_frame = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                data = encoded_frame.tobytes()
                size = len(data)
                client_socket.sendall(struct.pack(">L", size) + data)
        except Exception as e:
            print("Connection lost:", e)
        finally:
            client_socket.close()

if __name__ == '__main__':
    stream_camera()
