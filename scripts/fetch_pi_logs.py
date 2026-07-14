import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print("Fetching logs from Pi...")
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
        
        child.sendline('cat socat.log')
        child.expect(r'\$')
        print("--- SOCAT LOG ---")
        print(child.before.decode('utf-8'))
        
        child.sendline('cat camera.log')
        child.expect(r'\$')
        print("--- CAMERA LOG ---")
        print(child.before.decode('utf-8'))
        
        child.sendline('ls -l /dev/ttyUSB*')
        child.expect(r'\$')
        print("--- USB DEVICES ---")
        print(child.before.decode('utf-8'))
        
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
