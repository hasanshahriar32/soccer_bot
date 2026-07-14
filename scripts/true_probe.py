import pexpect

def main():
    ip = '192.168.0.135'
    user = 'hasan'
    password = 'grammarpro'
    
    probe_script = """
import serial
import time

for baud in [115200, 128000, 153600, 230400]:
    try:
        ser = serial.Serial('/dev/ttyUSB0', baud, timeout=1)
        ser.write(b'\\xA5\\x90') # Device Info
        time.sleep(0.5)
        data = ser.read(100)
        ser.close()
        
        if len(data) >= 2 and data[0] == 0xA5 and data[1] == 0x5A:
            print(f"BINGO! Correct baudrate is {baud}")
        else:
            print(f"Failed at {baud}: {data[:10].hex()}")
    except Exception as e:
        print(f"Error at {baud}: {e}")
"""

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
        
        child.sendline('killall python3')
        child.expect(r'\$')
        
        child.sendline("cat << 'EOF' > true_probe.py\n" + probe_script + "\nEOF")
        child.expect(r'\$')
        
        child.sendline('python3 true_probe.py')
        child.expect(r'\$')
        print(child.before.decode('utf-8'))
        
        child.sendline('exit')
    except Exception as e:
        print("SSH Error:", str(e))

if __name__ == '__main__':
    main()
