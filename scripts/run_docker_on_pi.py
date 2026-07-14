import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print("Connecting via SSH directly to avoid pxssh issues...")
    try:
        child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {user}@{ip}', timeout=30)
        
        i = child.expect(['[Pp]assword:', pexpect.EOF, 'Are you sure'])
        if i == 2:
            child.sendline('yes')
            child.expect('[Pp]assword:')
            child.sendline(password)
        elif i == 0:
            child.sendline(password)
            
        # Wait for bash prompt (usually ends with $)
        child.expect(r'\$')
        print("Logged in!")
        
        child.sendline('tar -xzf docker_deployment.tar.gz')
        child.expect(r'\$')
        print("Extracted files.")
        
        child.sendline('cd soccer_bot_docker')
        child.expect(r'\$')
        
        child.sendline('nohup docker compose up --build -d > docker_build.log 2>&1 &')
        child.expect(r'\$')
        print("Launched Docker compose in the background!")
        
        child.sendline('exit')
        print("Disconnected cleanly.")
    except Exception as e:
        print("SSH Error:", str(e))
        print("Buffer:", child.before.decode('utf-8'))

if __name__ == '__main__':
    main()
