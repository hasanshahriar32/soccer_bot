import serial
import socket
import threading
import sys
import time

def tcp_to_serial(conn, ser):
    try:
        while True:
            data = conn.recv(1024)
            if not data: break
            ser.write(data)
    except Exception as e:
        pass

def serial_to_tcp(conn, ser):
    try:
        while True:
            data = ser.read(1024)
            if data:
                conn.sendall(data)
    except Exception as e:
        pass

def main():
    baud = 115200 # Using 115200 as we suspect it is an X3 or similar
    try:
        ser = serial.Serial('/dev/ttyUSB0', baud, timeout=0.1)
        ser.setDTR(True)
        ser.setRTS(True)
        time.sleep(1)
        
        # CRITICAL FIX: Send STOP SCAN (A5 65) to force Lidar out of continuous scan mode!
        # If it's scanning, it ignores Health checks and causes the C++ SDK to fail!
        print("Sending STOP SCAN to Lidar...")
        ser.write(b'\\xA5\\x65')
        time.sleep(0.5)
        
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception as e:
        print("Failed to open serial:", e)
        sys.exit(1)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5000))
    server.listen(1)
    print("Listening on port 5000...")

    while True:
        conn, addr = server.accept()
        print("Connected:", addr)
        
        t1 = threading.Thread(target=tcp_to_serial, args=(conn, ser), daemon=True)
        t2 = threading.Thread(target=serial_to_tcp, args=(conn, ser), daemon=True)
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        conn.close()
        print("Connection closed.")

if __name__ == '__main__':
    main()
