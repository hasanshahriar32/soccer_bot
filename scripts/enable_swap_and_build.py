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
        
        print("Enabling 2GB Swap on Pi...")
        child.sendline(f'echo "{password}" | sudo -S fallocate -l 2G /swapfile')
        child.expect(r'\$')
        child.sendline(f'echo "{password}" | sudo -S chmod 600 /swapfile')
        child.expect(r'\$')
        child.sendline(f'echo "{password}" | sudo -S mkswap /swapfile')
        child.expect(r'\$')
        child.sendline(f'echo "{password}" | sudo -S swapon /swapfile')
        child.expect(r'\$')
        print("Swap Enabled!")
        
        print("Starting Docker Compose Build on Pi...")
        child.sendline('cd ~/soccer_bot && docker-compose build')
        # We don't wait for it to finish in this script, we just start it in a tmux or nohup?
        # Actually let's just use nohup so it doesn't block the ssh session
        child.sendline('nohup docker-compose build > docker_build.log 2>&1 &')
        child.expect(r'\$')
        
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
