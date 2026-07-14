import pexpect
import sys

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
        
        # We need to restart Docker natively
        print("Starting native Docker build on Pi (with Swap enabled)...")
        child.sendline('cd ~/soccer_bot/scripts/soccer_bot_docker')
        child.expect(r'\$')
        
        # We run the build in the background with nohup, since it takes 10+ minutes
        child.sendline('nohup bash -c "docker compose build && docker compose up -d" > docker_build.log 2>&1 &')
        child.expect(r'\$')
        
        print("Docker build started in the background on Pi. It will take 10-20 minutes, but it will never OOM now due to Swap!")
        child.sendline('exit')
        
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
