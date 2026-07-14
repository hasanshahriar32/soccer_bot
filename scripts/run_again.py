import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print("Connecting via SSH to Pi...")
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
        print("Logged in successfully!")
        
        # Stop pihole if it exists to free up RAM
        print("Disabling unnecessary processes (Pi-hole)...")
        child.sendline(f'echo "{password}" | sudo -S systemctl stop pihole-FTL')
        child.expect(r'\$')
        child.sendline(f'echo "{password}" | sudo -S systemctl disable pihole-FTL')
        child.expect(r'\$')
        
        # Check RAM
        child.sendline('free -h')
        child.expect(r'\$')
        print("--- Current RAM Usage ---")
        print(child.before.decode('utf-8'))
        
        # Go to docker directory and restart build
        child.sendline('cd ~/soccer_bot_docker')
        child.expect(r'\$')
        
        print("Checking previous Docker logs if any...")
        child.sendline('tail -n 10 docker_build.log')
        child.expect(r'\$')
        print(child.before.decode('utf-8'))
        
        print("Restarting Docker container build process...")
        child.sendline('nohup docker compose up --build -d > docker_build.log 2>&1 &')
        child.expect(r'\$')
        print("Docker build has been restarted in the background!")
        
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))
        print("Buffer:", child.before.decode('utf-8'))

if __name__ == '__main__':
    main()
