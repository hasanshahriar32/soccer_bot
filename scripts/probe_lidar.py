import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    probe_script = """
import serial
import time

for baud in [115200, 128000, 230400]:
    try:
        ser = serial.Serial('/dev/ttyUSB0', baud, timeout=1)
        ser.write(b'\\xA5\\x60') # YDLidar scan command
        time.sleep(0.5)
        data = ser.read(100)
        if len(data) > 0:
            print(f"SUCCESS at {baud} baud! Received {len(data)} bytes.")
        else:
            print(f"No response at {baud} baud.")
        ser.close()
    except Exception as e:
        print(f"Error at {baud}: {e}")
"""

    print("Probing Lidar Baudrate on Pi...")
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
        
        # Kill socat to free up the serial port
        child.sendline(f'echo "{password}" | sudo -S killall socat')
        child.expect(r'\$')
        
        # Install pyserial
        child.sendline("sudo apt-get install -y python3-serial")
        child.expect(r'\$')
        
        # Run probe script
        child.sendline("cat << 'EOF' > probe_lidar.py\n" + probe_script + "\nEOF")
        child.expect(r'\$')
        
        child.sendline("python3 probe_lidar.py")
        child.expect(r'\$')
        print(child.before.decode('utf-8'))
        
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
