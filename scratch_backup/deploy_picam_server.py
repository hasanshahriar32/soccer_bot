import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.0.135', username='hasan', password='grammarpro')

picam_code = """from picamera2 import Picamera2
from flask import Flask, Response
import cv2
import time

app = Flask(__name__)

print("Initializing Picamera2...")
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()
print("Picamera2 initialized successfully!")

def generate_frames():
    while True:
        frame = picam2.capture_array()
        ret, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        frame_bytes = buffer.tobytes()
        yield (b'--frame\\r\\n'
               b'Content-Type: image/jpeg\\r\\n\\r\\n' + frame_bytes + b'\\r\\n')

@app.route('/video')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
"""

client.exec_command("cat << 'EOF' > ~/picam_server.py\n" + picam_code + "\nEOF")
time.sleep(1)

client.exec_command("pkill -f rpicam ; pkill -f http_camera_server.py ; pkill -f picam_server.py")
time.sleep(1)

client.exec_command("nohup python3 ~/picam_server.py > ~/camera.log 2>&1 &")
time.sleep(3)

s, o, e = client.exec_command("cat ~/camera.log")
print("Picamera2 Log:\n", o.read().decode())
client.close()
