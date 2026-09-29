#!/usr/bin/env python3
"""
Live Ball Detector using Picamera2 and TFLite INT8 Quantized YOLOv8 Model.
Serves an MJPEG video stream on http://0.0.0.0:8000
Provides ROS 2 topic publishing /ball_position & /ball_class and LiDAR /scan fusion.
"""

import os
import sys
import time
import math
import json
import socket
import threading

os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"

from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2

# ==================== NATIVE ROS 2 SUPPORT (OPTIONAL) ====================
try:
    import rclpy
    from rclpy.node import Node as RosNode
    from geometry_msgs.msg import Point as RosPoint
    from std_msgs.msg import String as RosString
    from sensor_msgs.msg import LaserScan as RosLaserScan
    HAS_RCLPY = True
except ImportError:
    HAS_RCLPY = False
# =========================================================================

# ==================== CONFIGURATION ====================
MODEL_PATH = os.path.expanduser("~/ball_detector_pi/pi_inference/model_int8.tflite")
CONF_THRESHOLD = 0.40   # Confident detection threshold to prevent false positives
IOU_THRESHOLD = 0.45    # NMS IoU threshold
NUM_THREADS = 2        # Conservative CPU thread count for Pi 3B to prevent undervoltage brownouts
HTTP_PORT = 8000       # MJPEG video stream port
BRIDGE_PORT = 8001     # TCP bridge port for ROS 2 scan & ball topics

# Camera & LiDAR Extrinsics Calibration
CAMERA_FOV_H = math.radians(62.0)  # Raspberry Pi Camera V2 horizontal FOV (62.0 deg)
CAMERA_LIDAR_ANGLE_OFFSET = 0.0     # Angular offset between Camera & LiDAR in degrees
# Horizontal focal length in pixels for 640x480 resolution
FOCAL_LENGTH_PX = (640.0 / 2.0) / math.tan(CAMERA_FOV_H / 2.0)  # ~532.54 px

CLASS_NAMES = {0: "Tennis Ball", 1: "Cricket Ball"}
CLASS_COLORS = {
    0: (0, 255, 127),   # Vibrant Green (BGR)
    1: (0, 50, 255)     # Vibrant Red (BGR)
}
# =======================================================

latest_jpeg = None
lock = threading.Lock()

# LiDAR Scan state
latest_scan = [0.0] * 360
scan_lock = threading.Lock()

# Bridge Socket client connections
bridge_clients = []
bridge_lock = threading.Lock()

ros_native_node = None


def nms(boxes, scores, iou_thresh):
    if len(boxes) == 0:
        return []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(ovr <= iou_thresh)[0]
        order = order[inds + 1]
    return keep


class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/video']:
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            try:
                while True:
                    with lock:
                        frame_bytes = latest_jpeg
                    if frame_bytes is not None:
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', str(len(frame_bytes)))
                        self.end_headers()
                        self.wfile.write(frame_bytes)
                        self.wfile.write(b'\r\n')
                    time.sleep(0.03)
            except Exception:
                pass
        else:
            self.send_error(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def start_http_streamer():
    server = ThreadedHTTPServer(('0.0.0.0', HTTP_PORT), StreamingHandler)
    print(f"[INFO] MJPEG Streamer listening at http://0.0.0.0:{HTTP_PORT}", flush=True)
    server.serve_forever()


# ==================== ROS 2 BRIDGE SERVER ====================
def bridge_server_thread():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind(('0.0.0.0', BRIDGE_PORT))
        server_sock.listen(5)
        print(f"[INFO] ROS 2 Bridge TCP server listening on port {BRIDGE_PORT}...", flush=True)
        while True:
            client_sock, client_addr = server_sock.accept()
            print(f"[INFO] ROS 2 Bridge connected to {client_addr}!", flush=True)
            with bridge_lock:
                bridge_clients.append(client_sock)
            t = threading.Thread(target=handle_bridge_client, args=(client_sock,), daemon=True)
            t.start()
    except Exception as e:
        print(f"[ERROR] Bridge server error: {e}", flush=True)


def handle_bridge_client(sock):
    global latest_scan
    buf = ""
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk.decode('utf-8', errors='ignore')
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    if msg.get("type") == "scan":
                        ranges = msg.get("ranges", [])
                        if len(ranges) >= 360:
                            with scan_lock:
                                latest_scan = ranges[:360]
                except Exception:
                    pass
        except Exception:
            break

    with bridge_lock:
        if sock in bridge_clients:
            bridge_clients.remove(sock)
    try:
        sock.close()
    except Exception:
        pass
    print("[INFO] ROS 2 Bridge client disconnected.", flush=True)


def publish_ball_detection(distance_m, pixel_offset, angle_deg, label_name, score):
    # 1. Native ROS 2 Publishing if rclpy is available
    if HAS_RCLPY and ros_native_node is not None:
        try:
            pt = RosPoint(x=float(distance_m), y=float(pixel_offset), z=float(angle_deg))
            st = RosString(data=f"{label_name} {int(score * 100)}%")
            ros_native_node.pub_pos.publish(pt)
            ros_native_node.pub_cls.publish(st)
        except Exception:
            pass

    # 2. Bridge TCP Broadcast to ROS 2 camera_hub_node
    payload = json.dumps({
        "type": "ball",
        "x": round(float(distance_m), 4),
        "y": round(float(pixel_offset), 2),
        "z": round(float(angle_deg), 2),
        "label": label_name,
        "score": round(float(score), 3)
    }) + "\n"
    encoded = payload.encode('utf-8')

    with bridge_lock:
        dead = []
        for c in bridge_clients:
            try:
                c.sendall(encoded)
            except Exception:
                dead.append(c)
        for d in dead:
            bridge_clients.remove(d)


# ==================== MAIN INFERENCE LOOP ====================
def main():
    global latest_jpeg, ros_native_node

    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Model file not found at {MODEL_PATH}", flush=True)
        sys.exit(1)

    print(f"[INFO] Loading TFLite model from {MODEL_PATH} with {NUM_THREADS} threads...", flush=True)
    interpreter = tflite.Interpreter(model_path=MODEL_PATH, num_threads=NUM_THREADS)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_shape = input_details[0]['shape']
    input_dtype = input_details[0]['dtype']
    input_scale, input_zero_point = input_details[0]['quantization']

    output_dtype = output_details[0]['dtype']
    output_scale, output_zero_point = output_details[0]['quantization']

    if len(input_shape) == 4:
        if input_shape[1] == 3:  # NCHW [1, 3, H, W]
            net_h, net_w = input_shape[2], input_shape[3]
            is_nchw = True
        else:  # NHWC [1, H, W, 3]
            net_h, net_w = input_shape[1], input_shape[2]
            is_nchw = False
    else:
        net_h, net_w = 320, 320
        is_nchw = True

    print(f"[INFO] Input Tensor Shape: {input_shape} (NCHW={is_nchw}), dtype={input_dtype}", flush=True)

    # Start Background Servers
    t_http = threading.Thread(target=start_http_streamer, daemon=True)
    t_http.start()

    t_bridge = threading.Thread(target=bridge_server_thread, daemon=True)
    t_bridge.start()

    # Optional Native ROS 2 Node
    if HAS_RCLPY:
        try:
            rclpy.init()
            class NativeNode(RosNode):
                def __init__(self):
                    super().__init__('pi_ball_detector_native')
                    self.pub_pos = self.create_publisher(RosPoint, '/ball_position', 10)
                    self.pub_cls = self.create_publisher(RosString, '/ball_class', 10)
                    self.sub_scan = self.create_subscription(RosLaserScan, '/scan', self.scan_cb, 10)
                def scan_cb(self, msg):
                    global latest_scan
                    if len(msg.ranges) >= 360:
                        with scan_lock:
                            latest_scan = list(msg.ranges[:360])
            ros_native_node = NativeNode()
            t_ros = threading.Thread(target=lambda: rclpy.spin(ros_native_node), daemon=True)
            t_ros.start()
            print("[INFO] Native rclpy initialized and spinning successfully.", flush=True)
        except Exception as e:
            print(f"[WARN] Native rclpy init skipped ({e}). Operating in Bridge mode.", flush=True)

    cam_w, cam_h = 640, 480
    print(f"[INFO] Initializing Picamera2 with format RGB888 ({cam_w}x{cam_h})...", flush=True)
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(main={"size": (cam_w, cam_h), "format": "RGB888"})
    picam2.configure(video_config)
    picam2.start()

    cam_cfg = picam2.camera_configuration()
    print("=== CONFIRMED CAMERA CONFIGURATION ===", flush=True)
    print(f"Main format: {cam_cfg.get('main', {}).get('format')}", flush=True)
    print(f"Main size:   {cam_cfg.get('main', {}).get('size')}", flush=True)
    print(f"Colourspace: {cam_cfg.get('colour_space')}", flush=True)
    print(f"Camera FOV:  {math.degrees(CAMERA_FOV_H):.1f}° (Focal Length: {FOCAL_LENGTH_PX:.1f}px)", flush=True)
    print("=======================================", flush=True)

    fps_avg = 0.0
    frame_count = 0
    last_debug_time = time.time()

    try:
        while True:
            t_start = time.time()

            # 1. Capture raw array from Picamera2 (BGR memory layout)
            raw_bgr = picam2.capture_array()
            # Physical camera is mounted upside down: reverse vertically (bottom side up, up side bottom)
            raw_bgr = cv2.flip(raw_bgr, 0)
            orig_h, orig_w, _ = raw_bgr.shape

            # 2. Model Preprocessing: Convert BGR -> true RGB for YOLOv8 model inference
            img_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)

            if orig_w != net_w or orig_h != net_h:
                resized_rgb = cv2.resize(img_rgb, (net_w, net_h), interpolation=cv2.INTER_LINEAR)
            else:
                resized_rgb = img_rgb

            img_float = resized_rgb.astype(np.float32) / 255.0

            if input_dtype == np.int8:
                if input_scale != 0:
                    input_data = (img_float / input_scale + input_zero_point)
                else:
                    input_data = (img_float - 0.5) * 255.0
                input_data = np.clip(input_data, -128, 127).astype(np.int8)
            elif input_dtype == np.uint8:
                if input_scale != 0:
                    input_data = (img_float / input_scale + input_zero_point)
                else:
                    input_data = img_float * 255.0
                input_data = np.clip(input_data, 0, 255).astype(np.uint8)
            else:  # float32
                input_data = img_float.astype(np.float32)

            if is_nchw:
                input_data = np.transpose(input_data, (2, 0, 1))

            input_tensor = np.expand_dims(input_data, axis=0)

            # 3. Execute TFLite Model Inference
            interpreter.set_tensor(input_details[0]['index'], input_tensor)
            interpreter.invoke()
            raw_output = interpreter.get_tensor(output_details[0]['index'])

            if output_dtype in [np.int8, np.uint8]:
                output_data = (raw_output.astype(np.float32) - output_zero_point) * output_scale
            else:
                output_data = raw_output

            preds = np.squeeze(output_data)
            if preds.shape[0] == 6 and preds.shape[1] != 6:
                preds = preds.T  # Shape: (2100, 6)

            boxes = []
            scores = []
            class_ids = []

            max_coord = max(preds[:, 0].max(), preds[:, 1].max())
            if max_coord <= 2.0:
                scale_x = orig_w
                scale_y = orig_h
            else:
                scale_x = orig_w / net_w
                scale_y = orig_h / net_h

            for row in preds:
                cls_scores = row[4:]
                cls_id = int(np.argmax(cls_scores))
                score = float(cls_scores[cls_id])

                if score >= CONF_THRESHOLD:
                    xc, yc, w, h = row[0], row[1], row[2], row[3]

                    x1 = (xc - w / 2.0) * scale_x
                    y1 = (yc - h / 2.0) * scale_y
                    x2 = (xc + w / 2.0) * scale_x
                    y2 = (yc + h / 2.0) * scale_y

                    x1 = max(0, min(orig_w, x1))
                    y1 = max(0, min(orig_h, y1))
                    x2 = max(0, min(orig_w, x2))
                    y2 = max(0, min(orig_h, y2))

                    boxes.append([x1, y1, x2, y2])
                    scores.append(score)
                    class_ids.append(cls_id)

            boxes = np.array(boxes)
            scores = np.array(scores)
            class_ids = np.array(class_ids)

            # 4. Stream Image: Use raw_bgr DIRECTLY for accurate rendering
            display_img = raw_bgr.copy()

            # Apply Non-Maximum Suppression (NMS) & LiDAR Distance Fusion
            detected_count = 0
            primary_detection = None

            if len(boxes) > 0:
                indices = nms(boxes, scores, IOU_THRESHOLD)
                detected_count = len(indices)

                with scan_lock:
                    scan_snapshot = list(latest_scan)

                for idx in indices:
                    b = boxes[idx]
                    sc = scores[idx]
                    cid = class_ids[idx]

                    x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
                    label_name = CLASS_NAMES.get(cid, f"Class {cid}")
                    color = CLASS_COLORS.get(cid, (255, 255, 255))

                    # 1. Convert bbox center's pixel x-offset to degree offset using camera FOV
                    cx = (x1 + x2) / 2.0
                    pixel_offset = float(cx - (orig_w / 2.0))
                    angle_offset_deg = math.degrees(math.atan2(pixel_offset, FOCAL_LENGTH_PX))

                    # 2. Look up angle's distance in latest /scan (YDLidar X4: index 0 = forward)
                    target_angle_deg = (angle_offset_deg + CAMERA_LIDAR_ANGLE_OFFSET) % 360.0

                    # Average +/- 2 deg, filter invalid readings (0.05m to 10.0m)
                    angles_to_check = [(int(round(target_angle_deg + d))) % 360 for d in range(-2, 3)]
                    valid_readings = [
                        scan_snapshot[a] for a in angles_to_check
                        if 0.05 < scan_snapshot[a] < 10.0 and not math.isnan(scan_snapshot[a]) and not math.isinf(scan_snapshot[a])
                    ]

                    if valid_readings:
                        distance_in_meters = float(sum(valid_readings) / len(valid_readings))
                        dist_tag = "LIDAR"
                    else:
                        # Optical pinhole fallback if LiDAR beam passes over/under target
                        ball_real_diam_m = 0.067 if cid == 0 else 0.072
                        box_w_px = max(1.0, float(x2 - x1))
                        distance_in_meters = float((ball_real_diam_m * FOCAL_LENGTH_PX) / box_w_px)
                        dist_tag = "OPT"

                    # Draw Bounding Box & HUD Label
                    cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 3)
                    text = f"{label_name} {int(sc * 100)}% | {distance_in_meters:.2f}m ({dist_tag})"
                    font_scale = 0.65
                    thickness = 2
                    (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)

                    bg_y1 = max(0, y1 - text_h - 10)
                    bg_y2 = y1
                    cv2.rectangle(display_img, (x1, bg_y1), (x1 + text_w + 10, bg_y2), color, -1)

                    text_y = max(text_h + 2, y1 - 5)
                    cv2.putText(display_img, text, (x1 + 5, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

                    # Select primary detection (highest confidence) for targeting
                    if primary_detection is None or sc > primary_detection[3]:
                        primary_detection = (distance_in_meters, pixel_offset, angle_offset_deg, sc, label_name)

            # Publish primary detection to ROS 2 topics
            if primary_detection is not None:
                dist_m, pix_off, ang_deg, sc, lbl = primary_detection
                publish_ball_detection(dist_m, pix_off, ang_deg, lbl, sc)

            t_end = time.time()
            fps_curr = 1.0 / max(1e-5, (t_end - t_start))
            fps_avg = 0.9 * fps_avg + 0.1 * fps_curr if frame_count > 0 else fps_curr
            frame_count += 1

            # HUD Telemetry & Center Aim Target
            fps_text = f"FPS: {fps_avg:.1f} | Detections: {detected_count}"
            cv2.rectangle(display_img, (5, 5), (320, 35), (0, 0, 0), -1)
            cv2.putText(display_img, fps_text, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.circle(display_img, (320, 240), 12, (255, 255, 0), 1)

            # Periodic diagnostic log
            now = time.time()
            if now - last_debug_time >= 2.0:
                if primary_detection is not None:
                    d_m, p_off, a_deg, sc, lbl = primary_detection
                    print(f"[DETECT & FUSE] 🎯 {lbl} ({int(sc*100)}%): Dist={d_m:.2f}m ({d_m*39.37:.1f}in), Offset={p_off:+.1f}px ({a_deg:+.1f}°)", flush=True)
                last_debug_time = now

            # 5. JPEG Encode
            ret, buffer = cv2.imencode('.jpg', display_img, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ret:
                with lock:
                    latest_jpeg = buffer.tobytes()
            time.sleep(0.03)

    except KeyboardInterrupt:
        print("[INFO] Stopping live inference...", flush=True)
    finally:
        picam2.stop()
        print("[INFO] Picamera2 stopped.", flush=True)


if __name__ == '__main__':
    main()
