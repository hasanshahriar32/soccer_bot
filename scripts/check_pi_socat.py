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
        
        child.sendline('cat socat.log')
        child.expect(r'\$')
        print("PI SOCAT LOG:")
        print(child.before.decode('utf-8'))
        
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
