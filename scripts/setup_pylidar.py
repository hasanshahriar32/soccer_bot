import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    edge_script = """
import PyLidar3
import socket
import json
import time

# Monkey-patch serial to FORCE 115200 baudrate and DTR=True
import serial
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
        print("Lidar ready, waiting for laptop...")
        while True:
            try:
                conn, addr = server.accept()
                print("Laptop connected!")
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

    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {user}@{ip}', timeout=30)
        i = child.expect(['[Pp]assword:', pexpect.EOF, 'Are you sure'])
        if i == 2:
            child.sendline('yes')
            child.expect('[Pp]assword:')
            child.sendline(password)
        elif i == 0:
            child.sendline(password)
            
        child.expect(r'\$')
        
        child.sendline('killall python3')
        child.expect(r'\$')
        
        child.sendline("cat << 'EOF' > edge_lidar.py\n" + edge_script + "\nEOF")
        child.expect(r'\$')
        
        print("Starting Edge Lidar Streamer...")
        child.sendline('nohup python3 -u edge_lidar.py > lidar.log 2>&1 &')
        child.expect(r'\$')
        
        print("Starting Edge Camera Streamer...")
        child.sendline('nohup python3 -u edge_node.py > camera.log 2>&1 &')
        child.expect(r'\$')
        
        child.sendline('exit')
        print("Pi successfully configured with patched PyLidar3!")
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
