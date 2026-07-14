import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
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
        
        # Kill old socat
        child.sendline('killall socat')
        child.expect(r'\$')
        
        # Start socat with 128000 baud
        child.sendline('nohup socat tcp-l:5000,reuseaddr,fork file:/dev/ttyUSB0,nonblock,b128000,cs8,raw,echo=0 > socat.log 2>&1 &')
        child.expect(r'\$')
        
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
