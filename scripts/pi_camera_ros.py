import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import subprocess
import numpy as np
import cv2
import threading

class PiCameraNode(Node):
    def __init__(self):
        super().__init__('pi_camera_node')
        self.publisher_ = self.create_publisher(Image, '/image_raw', 10)
        self.width = 640
        self.height = 480
        self.frame_size = int(self.width * self.height * 1.5) # YUV420 size
        
        self.get_logger().info("Starting rpicam-vid process...")
        
        # Start rpicam-vid outputting raw YUV420 to stdout
        cmd = [
            'rpicam-vid',
            '-t', '0',               # Run forever
            '--width', str(self.width),
            '--height', str(self.height),
            '--framerate', '15',
            '--codec', 'yuv420',
            '-o', '-'                # Output to stdout
        ]
        
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        # Start the reader thread
        self.thread = threading.Thread(target=self.read_frames)
        self.thread.daemon = True
        self.thread.start()
        
    def read_frames(self):
        while rclpy.ok():
            # Read exactly one frame of YUV420 data
            raw_data = self.process.stdout.read(self.frame_size)
            if len(raw_data) != self.frame_size:
                self.get_logger().error("Failed to read a full frame from camera!")
                continue
                
            # Convert raw bytes to numpy array
            yuv_array = np.frombuffer(raw_data, dtype=np.uint8).reshape((int(self.height * 1.5), self.width))
            
            # Convert YUV420 to BGR for standard ROS 2 processing
            bgr_image = cv2.cvtColor(yuv_array, cv2.COLOR_YUV2BGR_I420)
            
            # Create ROS 2 Image message manually (without cv_bridge to save dependencies)
            msg = Image()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'camera_frame'
            msg.height = self.height
            msg.width = self.width
            msg.encoding = 'bgr8'
            msg.is_bigendian = 0
            msg.step = self.width * 3
            msg.data = bgr_image.tobytes()
            
            self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = PiCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.process.terminate()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
