import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print("Checking Docker status on Raspberry Pi...")
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
        
        # Check running containers
        child.sendline('docker ps')
        child.expect(r'\$')
        print("--- Docker Containers ---")
        print(child.before.decode('utf-8'))
        
        # Check build logs
        child.sendline('tail -n 15 soccer_bot_docker/docker_build.log')
        child.expect(r'\$')
        print("--- Build Log Tail ---")
        print(child.before.decode('utf-8'))
        
        child.sendline('exit')
    except Exception as e:
        print("Error checking status:", str(e))

if __name__ == '__main__':
    main()
