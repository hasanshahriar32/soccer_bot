import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading
import time

class CameraHubNode(Node):
    def __init__(self):
        super().__init__('camera_hub_node')
        self.publisher_ = self.create_publisher(Image, '/image_raw', 5)
        self.bridge = CvBridge()
        self.url = 'http://192.168.0.135:8080/video'
        
        self.get_logger().info(f"Connecting to Camera stream at {self.url}...")
        self.running = True
        self.thread = threading.Thread(target=self.receive_stream)
        self.thread.daemon = True
        self.thread.start()

    def receive_stream(self):
        while self.running:
            try:
                cap = cv2.VideoCapture(self.url)
                if not cap.isOpened():
                    time.sleep(1.0)
                    continue
                    
                self.get_logger().info("Connected to Camera stream successfully!")
                
                last_pub = time.time()
                while self.running and cap.isOpened():
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        break
                        
                    now = time.time()
                    # Throttle to 10 FPS max so RViz never freezes
                    if now - last_pub >= 0.10:
                        last_pub = now
                        # Resize frame to 320x240 for super fast rendering
                        small_frame = cv2.resize(frame, (320, 240), interpolation=cv2.INTER_NEAREST)
                        msg = self.bridge.cv2_to_imgmsg(small_frame, "bgr8")
                        msg.header.stamp = self.get_clock().now().to_msg()
                        msg.header.frame_id = "camera_link"
                        self.publisher_.publish(msg)
                    
                cap.release()
            except Exception as e:
                time.sleep(1.0)

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
