import pexpect
from pexpect import pxssh
import sys

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    print("Step 1: Compressing workspace...")
    pexpect.run('tar -czf soccer_bot.tar.gz -C /home/sharmin/Desktop/iot soccer_bot')
    
    print("Step 2: Transferring workspace via SCP...")
    scp_cmd = f"scp -o StrictHostKeyChecking=no soccer_bot.tar.gz {user}@{ip}:~/"
    child = pexpect.spawn(scp_cmd, timeout=300)
    
    try:
        i = child.expect(['[Pp]assword:', pexpect.EOF])
        if i == 0:
            child.sendline(password)
            child.expect(pexpect.EOF)
    except Exception as e:
        print(f"SCP Warning: {e}")
        
    print("SCP Complete.")
    
    print("Step 3: Connecting via SSH to install Docker...")
    try:
        s = pxssh.pxssh(options={"StrictHostKeyChecking": "no", "UserKnownHostsFile": "/dev/null"}, timeout=600)
        s.login(ip, user, password)
        
        commands = [
            'tar -xzf soccer_bot.tar.gz',
            'curl -fsSL https://get.docker.com -o get-docker.sh',
            f'echo "{password}" | sudo -S sh get-docker.sh',
            f'echo "{password}" | sudo -S usermod -aG docker $USER'
        ]
        
        for cmd in commands:
            print(f"Executing: {cmd}")
            s.sendline(cmd)
            s.prompt()
            print(s.before.decode('utf-8'))
            
        s.logout()
        print("Deployment and Docker installation successful!")
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
