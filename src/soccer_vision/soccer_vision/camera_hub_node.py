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
        
        self.port = 8000
        
        self.get_logger().info(f"Listening for raw MJPEG TCP stream on port {self.port}...")
        
        self.running = True
        self.thread = threading.Thread(target=self.receive_stream)
        self.thread.daemon = True
        self.thread.start()

    def receive_stream(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.port))
        server_socket.listen(1)
        
        while self.running:
            try:
                self.get_logger().info("Waiting for Pi camera to connect...")
                server_socket.settimeout(2.0)
                try:
                    client_socket, addr = server_socket.accept()
                except socket.timeout:
                    continue
                    
                self.get_logger().info(f"Pi Camera connected from {addr}!")
                client_socket.settimeout(5.0)
                
                stream_bytes = b''
                while self.running:
                    data = client_socket.recv(1024 * 64)
                    if not data:
                        self.get_logger().info("Pi disconnected.")
                        break
                    stream_bytes += data
                    
                    a = stream_bytes.find(b'\xff\xd8')
                    b = stream_bytes.find(b'\xff\xd9')
                    
                    if a != -1 and b != -1 and b > a:
                        jpg = stream_bytes[a:b+2]
                        stream_bytes = stream_bytes[b+2:]
                        
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            # Display live camera preview window on screen
                            cv2.imshow("Soccer Bot - Pi Camera Feed", frame)
                            cv2.waitKey(1)

                            msg = self.bridge.cv2_to_imgmsg(frame, "bgr8")
                            msg.header.stamp = self.get_clock().now().to_msg()
                            msg.header.frame_id = "camera_link"
                            self.publisher_.publish(msg)
                            
            except Exception as e:
                self.get_logger().error(f"Stream error: {e}")
            finally:
                if 'client_socket' in locals():
                    client_socket.close()

def main(args=None):
    rclpy.init(args=args)
    node = CameraHubNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.running = False
        node.thread.join()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
