import pexpect
from pexpect import pxssh

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    try:
        s = pxssh.pxssh(options={"StrictHostKeyChecking": "no", "UserKnownHostsFile": "/dev/null"}, timeout=600)
        s.login(ip, user, password)
        
        commands = [
            # Fix the GPG key for cloudflare repo
            f'echo "{password}" | sudo -S curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg',
            f'echo "{password}" | sudo -S apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 254B391D8CACCBF8',
            f'echo "{password}" | sudo -S apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 8A682D308D4E5E73',
            # Re-run docker installation
            f'echo "{password}" | sudo -S sh get-docker.sh',
            f'echo "{password}" | sudo -S usermod -aG docker $USER'
        ]
        
        for cmd in commands:
            print(f"Executing: {cmd}")
            s.sendline(cmd)
            s.prompt()
            print(s.before.decode('utf-8'))
            
        s.logout()
        print("Fix and Docker installation complete!")
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
