import pexpect
import time

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    edge_node_code = """
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
"""

    print("Connecting via SSH to configure Lightweight Node...")
    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {user}@{ip}', timeout=600)
        
        i = child.expect(['[Pp]assword:', pexpect.EOF, 'Are you sure'])
        if i == 2:
            child.sendline('yes')
            child.expect('[Pp]assword:')
            child.sendline(password)
        elif i == 0:
            child.sendline(password)
            
        child.expect(r'\$')
        print("Logged into Pi!")
        
        # Install python-opencv and socat
        child.sendline(f'echo "{password}" | sudo -S apt-get update && sudo apt-get install -y python3-opencv socat')
        child.expect(r'\$')
        print("Installed lightweight dependencies.")
        
        # Write the edge_node.py to the Pi
        child.sendline("cat << 'EOF' > edge_node.py" + edge_node_code + "EOF")
        child.expect(r'\$')
        
        # Kill any existing processes
        child.sendline("killall socat python3")
        child.expect(r'\$')
        
        # Start socat for Lidar (Port 5000)
        print("Starting Lidar TCP Forwarder on port 5000...")
        child.sendline("nohup socat tcp-l:5000,reuseaddr,fork file:/dev/ttyUSB0,nonblock,b115200,cs8,raw,echo=0 > socat.log 2>&1 &")
        child.expect(r'\$')
        
        # Start Python Camera server (Port 5001)
        print("Starting Camera TCP Forwarder on port 5001...")
        child.sendline("nohup python3 edge_node.py > camera.log 2>&1 &")
        child.expect(r'\$')
        
        child.sendline('exit')
        print("Deployment to Pi successful! Sensors are now streaming live.")
        
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
