import sys
from pexpect import pxssh

def main():
    try:
        s = pxssh.pxssh(options={"StrictHostKeyChecking": "no", "UserKnownHostsFile": "/dev/null"})
        print("Connecting to Pi...")
        s.login('192.168.0.135', 'hasan', 'grammarpro')
        print("Successfully connected!")
        
        s.sendline('cat /etc/os-release')
        s.prompt()
        print(s.before.decode('utf-8'))
        
        s.sendline('uname -m')
        s.prompt()
        print("Architecture:", s.before.decode('utf-8'))
        
        s.logout()
    except Exception as e:
        print("Failed to connect:", str(e))

if __name__ == '__main__':
    main()
