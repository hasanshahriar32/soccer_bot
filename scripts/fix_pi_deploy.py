import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print("SCP'ing edge_node.py to Pi...")
    scp_cmd = f"scp -o StrictHostKeyChecking=no /home/sharmin/Desktop/iot/soccer_bot/scripts/edge_node.py {user}@{ip}:~/"
    child = pexpect.spawn(scp_cmd, timeout=30)
    try:
        i = child.expect(['[Pp]assword:', pexpect.EOF])
        if i == 0:
            child.sendline(password)
            child.expect(pexpect.EOF)
    except Exception as e:
        print(f"SCP Error: {e}")
        
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
        
        # Kill old processes
        child.sendline(f'echo "{password}" | sudo -S killall socat python3')
        child.expect(r'\$')
        
        # Start socat for Lidar (Port 5000) using SUDO!
        print("Starting Lidar TCP Forwarder on port 5000 (with sudo)...")
        child.sendline(f'nohup echo "{password}" | sudo -S socat tcp-l:5000,reuseaddr,fork file:/dev/ttyUSB0,nonblock,b115200,cs8,raw,echo=0 > socat.log 2>&1 &')
        child.expect(r'\$')
        
        # Start Python Camera server (Port 5001)
        print("Starting Camera TCP Forwarder on port 5001...")
        child.sendline("nohup python3 edge_node.py > camera.log 2>&1 &")
        child.expect(r'\$')
        
        child.sendline('exit')
        print("Sensors are now securely streaming live!")
        
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
