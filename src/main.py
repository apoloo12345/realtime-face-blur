# Dockerized Python Script with Integrated NGINX-RTMP Server for SRT Face Blur (CPU/GPU Support)
# --------------------------------------------------------------------------------------------
# This container:
# 1. Runs an NGINX server with RTMP module to serve the processed stream.
# 2. Listens to an SRT input stream, blurs detected faces, and pushes to the local RTMP server.
# 3. Supports both CPU and GPU for face detection based on the USE_GPU environment variable.
# 4. OBS can access the stream at rtmp://<host>:1935/live/blurred

import cv2
import numpy as np
import subprocess
import os
import sys

SRT_URL = os.getenv("SRT_URL", "srt://0.0.0.0:9000")
RTMP_URL = "rtmp://127.0.0.1:1935/live/blurred"
WIDTH = int(os.getenv("INPUT_WIDTH", 1280))
HEIGHT = int(os.getenv("INPUT_HEIGHT", 720))
FPS = int(os.getenv("INPUT_FPS", 30))
USE_GPU = int(os.getenv("USE_GPU", 0))

# Load OpenCV DNN face detector
face_net = cv2.dnn.readNetFromCaffe(
    "deploy.prototxt",
    "res10_300x300_ssd_iter_140000.caffemodel"
)

# Configure backend according to USE_GPU environment variable
if USE_GPU:
    try:
        face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        print("[INFO] Using GPU acceleration for face detection.")
    except Exception as e:
        print(f"[WARN] CUDA backend not available, falling back to CPU: {e}")
        face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
else:
    face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    print("[INFO] Using CPU for face detection.")

# Start local NGINX RTMP server in background
nginx_conf = "/etc/nginx/nginx.conf"
subprocess.Popen(["nginx", "-c", nginx_conf])

# Start FFmpeg to pull SRT input as rawvideo
ffmpeg_in = [
    "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
    "-i", SRT_URL,
    "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{WIDTH}x{HEIGHT}", "-"
]
try:
    p_in = subprocess.Popen(ffmpeg_in, stdout=subprocess.PIPE, bufsize=10**8)
except Exception as e:
    print(f"[ERROR] Failed to start FFmpeg SRT input: {e}", file=sys.stderr)
    sys.exit(1)

# Start FFmpeg to push processed output to the local RTMP server
ffmpeg_out = [
    "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
    "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
    "-c:v", "h264_nvenc" if USE_GPU else "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
    "-f", "flv", RTMP_URL
]
try:
    p_out = subprocess.Popen(ffmpeg_out, stdin=subprocess.PIPE)
except Exception as e:
    print(f"[ERROR] Failed to start FFmpeg RTMP output: {e}", file=sys.stderr)
    sys.exit(1)

frame_size = WIDTH * HEIGHT * 3

while True:
    raw_frame = p_in.stdout.read(frame_size)
    if not raw_frame or len(raw_frame) != frame_size:
        print("[WARN] SRT stream interrupted or ended, retrying...", file=sys.stderr)
        break
    frame = np.frombuffer(raw_frame, np.uint8).reshape((HEIGHT, WIDTH, 3))

    # Face detection using DNN
    try:
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        face_net.setInput(blob)
        detections = face_net.forward()
    except Exception as e:
        print(f"[ERROR] Face detection failed: {e}", file=sys.stderr)
        continue

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            box = detections[0, 0, i, 3:7] * np.array([WIDTH, HEIGHT, WIDTH, HEIGHT])
            (x, y, x2, y2) = box.astype("int")
            x, y = max(0, x), max(0, y)
            face = frame[y:y2, x:x2]
            if face.size != 0:
                frame[y:y2, x:x2] = cv2.GaussianBlur(face, (51, 51), 30)

    try:
        p_out.stdin.write(frame.tobytes())
    except Exception as e:
        print(f"[ERROR] Failed to write to RTMP output: {e}", file=sys.stderr)
        break