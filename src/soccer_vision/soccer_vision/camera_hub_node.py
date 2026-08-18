import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import socket
import numpy as np
import threading
import time

class CameraHubNode(Node):
    def __init__(self):
        super().__init__('camera_hub_node')
        self.publisher_ = self.create_publisher(Image, '/image_raw', 10)
        self.bridge = CvBridge()
        self.pi_ip = '192.168.0.135'
        self.port = 8088
        self.running = True
        
        self.get_logger().info(f"Camera Hub Node started, connecting to rpicam-vid stream at {self.pi_ip}:{self.port}...")
        self.thread = threading.Thread(target=self.receive_stream, daemon=True)
        self.thread.start()

    def receive_stream(self):
        frame_cnt = 0
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((self.pi_ip, self.port))
                self.get_logger().info(f"Connected to Pi Camera rpicam stream at {self.pi_ip}:{self.port}!")
                
                stream_bytes = b''
                while self.running:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    stream_bytes += chunk
                    
                    a = stream_bytes.find(b'\xff\xd8')
                    b = stream_bytes.find(b'\xff\xd9')
                    if a != -1 and b != -1 and b > a:
                        jpg = stream_bytes[a : b + 2]
                        stream_bytes = stream_bytes[b + 2 :]
                        
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            msg = self.bridge.cv2_to_imgmsg(frame, "bgr8")
                            msg.header.stamp = self.get_clock().now().to_msg()
                            msg.header.frame_id = "camera_link"
                            self.publisher_.publish(msg)
                            
                            frame_cnt += 1
                            if frame_cnt % 60 == 0:
                                self.get_logger().info(f"Published {frame_cnt} camera frames to /image_raw")
                                
                sock.close()
            except Exception as e:
                time.sleep(1.0)

def main(args=None):
    rclpy.init(args=args)
    node = CameraHubNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.running = False
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
