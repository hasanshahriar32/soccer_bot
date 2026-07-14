import pexpect
import time

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print("Connecting via SSH...")
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
        
        # 1. Add user to dialout so sudo isn't needed
        child.sendline(f'echo "{password}" | sudo -S usermod -aG dialout {user}')
        child.expect(r'\$')
        
        # 2. Fix the camera script to force V4L2 instead of GStreamer
        child.sendline("sed -i 's/cv2.VideoCapture(0)/cv2.VideoCapture(0, cv2.CAP_V4L2)/g' edge_node.py")
        child.expect(r'\$')
        
        # 3. Kill old processes
        child.sendline(f'echo "{password}" | sudo -S killall socat python3')
        child.expect(r'\$')
        
        # IMPORTANT: Apply new group permissions by running the rest of the commands in a new login shell!
        child.sendline(f'su - {user}')
        child.expect('[Pp]assword:')
        child.sendline(password)
        child.expect(r'\$')
        
        # 4. Start socat WITHOUT sudo!
        print("Starting Lidar TCP Forwarder on port 5000...")
        child.sendline('nohup socat tcp-l:5000,reuseaddr,fork file:/dev/ttyUSB0,nonblock,b115200,cs8,raw,echo=0 > socat.log 2>&1 &')
        child.expect(r'\$')
        
        # 5. Start Python Camera server
        print("Starting Camera TCP Forwarder on port 5001...")
        child.sendline("nohup python3 edge_node.py > camera.log 2>&1 &")
        child.expect(r'\$')
        
        child.sendline('exit')
        child.expect(r'\$')
        child.sendline('exit')
        print("Pi fixes applied! Streaming started.")
        
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
