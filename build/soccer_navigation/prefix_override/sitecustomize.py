import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/sharmin/Desktop/iot/soccer_bot/install/soccer_navigation'
