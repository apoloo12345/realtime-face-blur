import cv2
import numpy as np
import subprocess
import os
import sys
import time
import json
import threading

# Ensure Python always flushes logs
sys.stdout.reconfigure(line_buffering=True)

INPUT_URL = os.getenv("INPUT_URL", "srt://host:port?streamid=play/stream/streamkey")
RTMP_URL = "rtmp://127.0.0.1:1935/live/blurred"
PROCESSED_VIDEO_URL = "rtmp://127.0.0.1:1935/live/video_only"
WIDTH = int(os.getenv("INPUT_WIDTH", 1920))
HEIGHT = int(os.getenv("INPUT_HEIGHT", 1080))
FPS = int(os.getenv("INPUT_FPS", 30))
USE_GPU = int(os.getenv("USE_GPU", 1))

def log(msg, level="INFO"):
    print(f"[PY][{level}] {msg}", flush=True)

face_net = cv2.dnn.readNetFromCaffe("deploy.prototxt", "res10_300x300_ssd_iter_140000.caffemodel")
if USE_GPU:
    try:
        face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        log("Using GPU acceleration for face detection.")
    except:
        log("CUDA not available → falling back to CPU.", "WARN")
        face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
else:
    face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    log("Using CPU for face detection.")

subprocess.Popen(["nginx", "-c", "/etc/nginx/nginx.conf"])

def is_h264(url):
    try:
        out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", url],
                             capture_output=True, text=True, timeout=10)
        info = json.loads(out.stdout)
        for s in info.get("streams", []):
            if s.get("codec_type") == "video":
                return s.get("codec_name") == "h264", s.get("codec_name")
    except:
        return False, "unknown"
    return False, "unknown"

def build_ffmpeg_input(url, use_gpu=True):
    """Builds FFmpeg command for decoding."""
    if use_gpu:
        log("Input is HEVC → using GPU decode and re-encoding to H.264.")
        return [
            "ffmpeg", "-loglevel", "error",
            "-hwaccel", "cuda", "-c:v", "hevc_cuvid",
            "-i", url,
            "-vf", f"hwdownload,format=bgr24,scale={WIDTH}:{HEIGHT}",
            "-pix_fmt", "bgr24",
            "-f", "rawvideo", "-"
        ]
    else:
        log("Falling back to software decode (libx264).", "WARN")
        return [
            "ffmpeg", "-loglevel", "error", "-fflags", "+genpts",
            "-i", url,
            "-vf", f"scale={WIDTH}:{HEIGHT}",
            "-pix_fmt", "bgr24", "-f", "rawvideo", "-"
        ]

def start_encoder():
    return subprocess.Popen([
        "ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
        "-c:v", "h264_nvenc" if USE_GPU else "libx264",
        "-preset", "ll" if USE_GPU else "veryfast",
        "-tune", "hq" if USE_GPU else "zerolatency",
        "-f", "flv", PROCESSED_VIDEO_URL
    ], stdin=subprocess.PIPE)

def start_muxer():
    return subprocess.Popen([
        "ffmpeg", "-loglevel", "error", "-fflags", "+genpts", "-use_wallclock_as_timestamps", "1",
        "-i", PROCESSED_VIDEO_URL, "-vn", "-i", INPUT_URL,
        "-map", "0:v:0", "-map", "1:a:0?",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        "-f", "flv", RTMP_URL
    ])

def process_stream():
    _, codec = is_h264(INPUT_URL)
    log(f"Detected codec: {codec}")
    muxer = start_muxer()

    for try_gpu in [True, False]:
        cmd = build_ffmpeg_input(INPUT_URL, use_gpu=try_gpu)
        log(f"FFmpeg input command: {' '.join(cmd)}", "DEBUG")

        try:
            p_in = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)
            encoder = start_encoder()
        except Exception as e:
            log(f"Failed to start FFmpeg: {e}", "ERROR")
            muxer.kill()
            return False

        frame_size = WIDTH * HEIGHT * 3
        start_time = time.time()

        while True:
            raw = p_in.stdout.read(frame_size)
            if not raw or len(raw) != frame_size:
                if time.time() - start_time > 5:
                    log("No frames received within 5s → restarting decode...", "WARN")
                    p_in.kill(); encoder.kill()
                    break
                continue

            frame = np.frombuffer(raw, np.uint8).reshape((HEIGHT, WIDTH, 3))
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
            face_net.setInput(blob)
            detections = face_net.forward()

            for i in range(detections.shape[2]):
                if detections[0, 0, i, 2] > 0.5:
                    x1, y1, x2, y2 = (detections[0, 0, i, 3:7] * np.array([WIDTH, HEIGHT, WIDTH, HEIGHT])).astype(int)
                    x1, y1 = max(0, x1), max(0, y1)
                    roi = frame[y1:y2, x1:x2]
                    if roi.size:
                        frame[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (51, 51), 30)

            try:
                encoder.stdin.write(frame.tobytes())
            except Exception as e:
                log(f"Encoder write failed: {e}", "ERROR")
                p_in.kill(); encoder.kill()
                muxer.kill()
                return False

        # retry with next mode (fallback)
    muxer.kill()
    return False

log("main.py started", "DEBUG")

while True:
    if not process_stream():
        log("Restarting stream processing in 5s...", "WARN")
        time.sleep(5)
