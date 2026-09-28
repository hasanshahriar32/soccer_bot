import pexpect
import time
import subprocess

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print("1. Launching Pi Sensors...")
    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {user}@{ip}', timeout=15)
        i = child.expect(['[Pp]assword:', pexpect.EOF, 'Are you sure'])
        if i == 2:
            child.sendline('yes')
            child.expect('[Pp]assword:')
            child.sendline(password)
        elif i == 0:
            child.sendline(password)
            
        child.expect(r'\$')
        
        child.sendline('killall socat python3')
        child.expect(r'\$')
        
        with open('scripts/python_socat.py', 'r') as f:
            script_code = f.read()
        
        child.sendline("cat << 'EOF' > python_socat.py\n" + script_code + "\nEOF")
        child.expect(r'\$')
        
        # Start python_socat and edge_node
        child.sendline('nohup python3 python_socat.py > socat.log 2>&1 &')
        child.expect(r'\$')
        child.sendline('nohup python3 edge_node.py > camera.log 2>&1 &')
        child.expect(r'\$')
        time.sleep(1) # wait for it to detach properly
        
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))
        return
        
    print("Pi Sensors started!")
    time.sleep(2)
    
    print("2. Starting Laptop Hub...")
    subprocess.run(['bash', '/home/sharmin/Desktop/iot/soccer_bot/scripts/start_laptop_hub.sh'])

if __name__ == '__main__':
    main()
