import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import socket
import numpy as np
import threading
import time

import struct

class CameraHubNode(Node):
    def __init__(self):
        super().__init__('camera_hub_node')
        self.publisher_ = self.create_publisher(Image, '/image_raw', 10)
        self.bridge = CvBridge()
        self.pi_ip = '192.168.0.135'
        self.port = 8000
        self.running = True
        
        print(f"[CameraHub] Node started, connecting to Pi Camera at {self.pi_ip}:{self.port}...", flush=True)
        self.get_logger().info(f"Camera Hub Node started, connecting to Pi Camera at {self.pi_ip}:{self.port}...")
        self.thread = threading.Thread(target=self.receive_stream, daemon=True)
        self.thread.start()

    def receive_stream(self):
        import urllib.request
        payload_size = struct.calcsize(">L")
        frame_cnt = 0
        while self.running:
            # 1. Strategy A: HTTP MJPEG Stream (detect_live_picamera2.py)
            http_success = False
            try:
                url = f"http://{self.pi_ip}:{self.port}/video"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    print(f"[CameraHub] Connected to Pi Camera HTTP Stream at {url}!", flush=True)
                    self.get_logger().info(f"Connected to Pi Camera HTTP Stream at {url}!")
                    stream_bytes = b""
                    while self.running:
                        chunk = resp.read(16384)
                        if not chunk:
                            break
                        stream_bytes += chunk
                        a = stream_bytes.find(b'\xff\xd8')
                        b = stream_bytes.find(b'\xff\xd9', a + 2) if a != -1 else -1
                        if a != -1 and b != -1:
                            jpg = stream_bytes[a:b+2]
                            stream_bytes = stream_bytes[b+2:]
                            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                msg = self.bridge.cv2_to_imgmsg(frame, "bgr8")
                                msg.header.stamp = self.get_clock().now().to_msg()
                                msg.header.frame_id = "camera_link"
                                self.publisher_.publish(msg)
                                frame_cnt += 1
                                if frame_cnt % 30 == 0:
                                    print(f"[CameraHub] Published {frame_cnt} frames to /image_raw", flush=True)
                                    self.get_logger().info(f"Published {frame_cnt} camera frames to /image_raw")
                                http_success = True
            except Exception:
                pass

            if http_success:
                continue

            # 2. Strategy B: Raw TCP size-prefixed socket (fast_camera_server.py)
            s = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(3.0)
                s.connect((self.pi_ip, self.port))
                print(f"[CameraHub] Connected to Pi Camera TCP Stream at {self.pi_ip}:{self.port}!", flush=True)
                self.get_logger().info(f"Connected to Pi Camera TCP Stream at {self.pi_ip}:{self.port}!")
                
                data = b""
                while self.running:
                    # 1. Read 4-byte payload size
                    while len(data) < payload_size:
                        packet = s.recv(4096)
                        if not packet:
                            break
                        data += packet
                    if len(data) < payload_size:
                        break

                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack(">L", packed_msg_size)[0]

                    # 2. Read full JPEG frame
                    while len(data) < msg_size:
                        packet = s.recv(65536)
                        if not packet:
                            break
                        data += packet
                    if len(data) < msg_size:
                        break

                    jpg = data[:msg_size]
                    data = data[msg_size:]

                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        msg = self.bridge.cv2_to_imgmsg(frame, "bgr8")
                        msg.header.stamp = self.get_clock().now().to_msg()
                        msg.header.frame_id = "camera_link"
                        self.publisher_.publish(msg)
                        
                        frame_cnt += 1
                        if frame_cnt % 30 == 0:
                            print(f"[CameraHub] Published {frame_cnt} frames to /image_raw", flush=True)
                            self.get_logger().info(f"Published {frame_cnt} camera frames to /image_raw")
            except Exception as e:
                time.sleep(1.0)
            finally:
                if s:
                    try:
                        s.close()
                    except Exception:
                        pass
                    except Exception:
                        pass

def main(args=None):
    if not rclpy.ok():
        rclpy.init(args=args)
    node = CameraHubNode()
    try:
        rclpy.spin(node)
    except Exception:
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception:
                pass

if __name__ == '__main__':
    main()
