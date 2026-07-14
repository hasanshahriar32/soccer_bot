import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {user}@{ip}', timeout=10)
        i = child.expect(['[Pp]assword:', pexpect.EOF, 'Are you sure'])
        if i == 2:
            child.sendline('yes')
            child.expect('[Pp]assword:')
            child.sendline(password)
        elif i == 0:
            child.sendline(password)
            
        child.expect(r'\$')
        
        child.sendline('socat tcp-l:5000,reuseaddr,fork file:/dev/ttyUSB0,nonblock,b128000,cs8,raw,echo=0')
        # Wait to see if it prints an error immediately
        try:
            child.expect(r'\$', timeout=3)
            print("Socat exited early:", child.before.decode('utf-8'))
        except pexpect.TIMEOUT:
            print("Socat is running successfully in foreground.")
            child.sendline('\x03') # Ctrl+C
            
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
