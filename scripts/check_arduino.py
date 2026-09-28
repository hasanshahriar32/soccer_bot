import paramiko
import time

def main():
    print("=" * 55)
    print("       AUDITING ARDUINO SERIAL CONNECTION ON PI")
    print("=" * 55)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.135', username='hasan', password='grammarpro', timeout=8)
    
    # 1. Check USB devices
    print("\n[Step 1] Enumerating USB Devices (lsusb):")
    stdin, stdout, stderr = ssh.exec_command('lsusb')
    print(stdout.read().decode().strip())
    
    # 2. Check Serial Ports (/dev/ttyACM* and /dev/ttyUSB*)
    print("\n[Step 2] Checking Serial Device Nodes (/dev/tty*):")
    stdin, stdout, stderr = ssh.exec_command('ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "No /dev/ttyUSB or /dev/ttyACM found"')
    ports_out = stdout.read().decode().strip()
    print(ports_out)
    
    # 3. Check kernel dmesg for recent Arduino connection
    print("\n[Step 3] Kernel Serial Log (dmesg):")
    stdin, stdout, stderr = ssh.exec_command('dmesg | grep -E "ttyUSB|ttyACM|ch341|ftdi|cdc_acm" | tail -n 10')
    print(stdout.read().decode().strip())
    
    # 4. Interactive Serial Probe
    print("\n[Step 4] Probing Serial Communication with Python on Pi:")
    test_code = """
import serial, glob, time
ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
print('Discovered Ports:', ports)
for p in ports:
    for baud in [115200, 57600, 9600]:
        try:
            s = serial.Serial(p, baud, timeout=1.0)
            time.sleep(0.5)
            s.write(b'\\n')
            resp = s.read(64)
            print(f'Port {p} @ {baud} baud: Open OK! Received {len(resp)} bytes: {resp}')
            s.close()
            break
        except Exception as e:
            print(f'Port {p} @ {baud} baud: {e}')
"""
    stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{test_code}"')
    print(stdout.read().decode().strip())
    
    ssh.close()
    print("\n" + "=" * 55)

if __name__ == '__main__':
    main()
