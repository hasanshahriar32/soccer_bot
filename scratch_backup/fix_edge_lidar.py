import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

fixed_edge_lidar = """import serial
import time
import socket
import json
import PyLidar3

print("Resetting Lidar hardware over serial...")
try:
    s = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.5)
    s.setDTR(True)
    s.setRTS(True)
    s.write(b'\\xA5\\x65') # STOP SCAN command
    time.sleep(0.5)
    s.reset_input_buffer()
    s.close()
    time.sleep(0.5)
except Exception as e:
    print("Serial reset warning:", e)

# Monkey-patch serial for PyLidar3
original_serial = serial.Serial
class FixedSerial(original_serial):
    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            args = list(args)
            args[1] = 115200
        elif 'baudrate' in kwargs:
            kwargs['baudrate'] = 115200
        super().__init__(*args, **kwargs)
        self.setDTR(True)
        self.setRTS(True)
serial.Serial = FixedSerial

def main():
    port = "/dev/ttyUSB0"
    Obj = PyLidar3.YdLidarX4(port)
    if Obj.Connect():
        print("Lidar Connected Successfully!")
        gen = Obj.StartScanning()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 5000))
        server.listen(1)
        print("Lidar TCP Server listening on port 5000...")
        while True:
            try:
                conn, addr = server.accept()
                print("Laptop connected:", addr)
                for scan in gen:
                    data = json.dumps(scan) + "\\n"
                    conn.sendall(data.encode('utf-8'))
            except Exception as e:
                print("Error:", e)
                try: conn.close()
                except: pass
        Obj.StopScanning()
        Obj.Disconnect()
    else:
        print("Error connecting to device")

if __name__ == "__main__":
    main()
"""

client.exec_command("cat << 'EOF' > ~/edge_lidar.py\n" + fixed_edge_lidar + "\nEOF")
time.sleep(1)

client.exec_command("sudo killall -9 python3 ydlidar_ros2_driver_node ; docker stop soccer_bot_edge")
time.sleep(2)

client.exec_command("nohup python3 ~/edge_lidar.py > ~/lidar.log 2>&1 &")
time.sleep(3)

s, o, e = client.exec_command("cat ~/lidar.log")
print("Lidar log output:\n", o.read().decode())
client.close()
