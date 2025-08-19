# Realtime Face Blur for Live Streams with Docker — RTMP/SRT

[![Releases](https://img.shields.io/github/v/release/apoloo12345/realtime-face-blur?label=Releases&logo=github)](https://github.com/apoloo12345/realtime-face-blur/releases)

![Live Blur Demo](https://raw.githubusercontent.com/apoloo12345/realtime-face-blur/main/docs/images/blur-sample.jpg)

A dockerized, low-latency face blurring service for live video streams. The project uses OpenCV and modern face detectors to blur faces in real time. It supports RTMP, SRT, HTTP and HTTPS inputs and outputs. Use it to protect privacy on public streams or record anonymized archives.

Releases: download the release asset named realtime-face-blur-release.tar.gz from the Releases page and execute the included run.sh file to start the packaged binary. Visit the Releases page to get the file: https://github.com/apoloo12345/realtime-face-blur/releases

Badges
- Build: [![build status](https://img.shields.io/github/actions/workflow/status/apoloo12345/realtime-face-blur/ci.yml?branch=main&logo=github)](https://github.com/apoloo12345/realtime-face-blur/actions)
- Python: [![python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org)
- Docker: [![docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://www.docker.com)
- License: [![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/apoloo12345/realtime-face-blur/blob/main/LICENSE)

Table of contents
- About
- Key features
- Architecture
- Images and demo links
- Quick start (Docker)
- Download and run releases
- Inputs and outputs
- Configuration
- Face detection options
- Performance tuning
- Security and HTTPS
- Logging and metrics
- Deployment examples
- Docker Compose
- Kubernetes
- Development
- Testing
- Troubleshooting
- FAQ
- Contributing
- License
- Credits

About
This repo contains a tool that blurs faces in live video streams. It runs in Docker. It accepts RTMP and SRT input streams. It can output to RTMP, SRT, or an HTTP endpoint that serves HLS. The core uses OpenCV and a choice of face detectors. You can choose CPU or GPU acceleration.

Key features
- Real time face detection and blur.
- Docker image that runs the complete pipeline.
- Support for RTMP and SRT input and output.
- HTTP/HTTPS streaming and HLS output.
- Selectable face detector backends (Haar, DNN, MTCNN).
- GPU options with CUDA and TensorRT hooks.
- Low latency design with frame queues and worker threads.
- Config via environment variables or YAML.
- Metrics via Prometheus endpoint.
- Swappable blur methods: Gaussian, pixelate, mosaic.
- Save anonymized recordings locally or to S3.

Architecture
- Input layer
  - RTMP/SRT ingest via FFmpeg or libsrt.
  - HTTP pull for HLS or MJPEG.
- Processing layer
  - Frame capture with OpenCV.
  - Face detection backend.
  - Blur module applies mask and composite.
  - Encoder prepares output stream.
- Output layer
  - RTMP/SRT push to destination.
  - HLS segmenter for HTTP delivery.
  - Local recording with MP4 or MKV.
- Control
  - REST API for health and commands.
  - Metrics endpoint for Prometheus.
- Container
  - Main service runs in a single container.
  - Optional sidecar for monitoring or storage.

Images and demo
- Input frame with faces: https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg
- Blur demo: https://raw.githubusercontent.com/apoloo12345/realtime-face-blur/main/docs/images/blur-sample.jpg
- Architecture diagram: https://raw.githubusercontent.com/apoloo12345/realtime-face-blur/main/docs/images/architecture.png

Quick start (Docker)
This quick start assumes you have Docker installed. It runs the default pipeline with RTMP input and RTMP output.

1. Pull the image
   docker pull ghcr.io/apoloo12345/realtime-face-blur:latest

2. Run the container
   docker run --rm \
     -e INPUT_URL="rtmp://0.0.0.0/live/stream" \
     -e OUTPUT_URL="rtmp://example.com/live/blurred" \
     -p 8080:8080 \
     ghcr.io/apoloo12345/realtime-face-blur:latest

3. Send a stream to the input URL using ffmpeg
   ffmpeg -re -i sample.mp4 -c copy -f flv rtmp://localhost/live/stream

4. View the output on your RTMP server or HLS endpoint.

Download and run releases
Download the release asset realtime-face-blur-release.tar.gz from the Releases page and execute the included run.sh to run the packaged binary. The release bundle contains:
- run.sh — startup script
- realtime-face-blur — compiled executable or packaged Python virtualenv
- config.yml — example configuration
- models/ — prebuilt detector models

To install from release on Linux:
- curl -L -o realtime-face-blur-release.tar.gz https://github.com/apoloo12345/realtime-face-blur/releases/download/v1.0.0/realtime-face-blur-release.tar.gz
- tar xzf realtime-face-blur-release.tar.gz
- cd realtime-face-blur-release
- chmod +x run.sh
- ./run.sh --config config.yml

If the release URL changes, visit the Releases page: https://github.com/apoloo12345/realtime-face-blur/releases

Inputs and outputs
Supported inputs
- RTMP (push, flv)
- SRT (low latency)
- HTTP(S) pull (HLS, MJPEG)
- Local file (mp4, mkv) for tests
- USB or V4L2 camera for local capture

Supported outputs
- RTMP to CDN or server
- SRT to low-latency endpoint
- HLS segments for browsers
- Local MP4 recording
- HTTP MJPEG for preview
- ZeroMQ or WebSocket for processed frames

Examples
- RTMP input -> RTMP output
- SRT input -> HLS output
- File input -> local MP4 recording (faces blurred)
- Camera input -> HTTP MJPEG preview

Configuration
You can configure the service using environment variables or config.yml. The service reads environment variables first, then config file, then defaults.

Main environment variables
- INPUT_URL — input stream URL (rtmp://, srt://, http://)
- OUTPUT_URL — output stream URL
- DETECTOR — face detector: haar, dnn, mtcnn, yolov5
- BLUR_METHOD — gaussian, pixelate, mosaic
- BLUR_STRENGTH — integer, e.g., 15
- FRAME_RATE — target processing fps
- MAX_WORKERS — number of worker threads
- SAVE_RECORDING — true/false
- RECORDING_PATH — path to store recordings
- METRICS_PORT — Prometheus metrics port
- HTTP_PORT — control API port
- USE_GPU — true/false
- CUDA_DEVICE — CUDA device index

Sample config.yml
```yaml
input:
  url: rtmp://0.0.0.0/live/stream
output:
  url: rtmp://example.com/live/blurred
detector:
  type: dnn
  model: models/res10_300x300_ssd_iter_140000.caffemodel
blur:
  method: gaussian
  strength: 21
performance:
  frame_rate: 25
  max_workers: 4
recording:
  save: true
  path: /data/recordings
metrics:
  prometheus_port: 9090
  enabled: true
security:
  http_tls: false
  tls_cert: /etc/tls/cert.pem
  tls_key: /etc/tls/key.pem
```

Face detection options
- Haarcascade
  - Fast on CPU.
  - Works on frontal faces.
  - Use for low-power devices.
- OpenCV DNN (Caffe/Tensorflow)
  - Balanced speed and accuracy.
  - Good for production.
- MTCNN
  - Better detection for small faces.
  - Higher CPU cost.
- YOLO or RetinaFace
  - High accuracy.
  - Use GPU for real time at high resolution.

Blur methods
- Gaussian blur
  - Smooth result.
  - Use larger kernel to hide identity.
- Pixelate
  - Blocky effect.
  - Use block size to tune privacy.
- Mosaic
  - Similar to pixelate.
  - Use mosaic tiles.

Performance tuning
- Lower the input resolution before detection to reduce CPU usage.
- Use a lightweight detector with lower resolution for high fps.
- Use GPU when available for DNN detectors.
- Batch frames when network jitter is high.
- Use frame skipping to maintain real-time speed on slow machines.
- Set MAX_WORKERS to match CPU cores.
- Tune BLUR_STRENGTH to balance privacy and clarity.

GPU support
- The container image has a GPU tag for CUDA 11 and cuDNN.
- Use nvidia-docker or Docker with --gpus.
- Set USE_GPU=true and specify CUDA_DEVICE.
- For TensorRT, install the optional plugin and switch detector to yolov5-trt.

Security and HTTPS
- The app exposes a control API and metrics endpoint.
- Enable TLS for the HTTP API using TLS_CERT and TLS_KEY.
- For production, place a reverse proxy like NGINX or Envoy in front.
- Use secure credentials for any push to third-party RTMP servers.
- For SRT, use passphrases and SRTP where possible.

Logging and metrics
- Logs write to stdout for Docker logging.
- Use METRICS_PORT to expose Prometheus metrics.
- Exported metrics
  - frames_processed_total
  - faces_detected_total
  - processing_latency_ms
  - active_workers
- Use Grafana to visualize the metrics.
- Rotate recording files via a cron job or sidecar when saving.

Deployment examples

Single node Docker (example)
- Run the container with mapped volumes for recordings and models.
  docker run -d --name face-blur \
    -p 1935:1935 \
    -p 8080:8080 \
    -v /var/lib/face-blur/recordings:/data/recordings \
    -v /var/lib/face-blur/models:/app/models \
    -e INPUT_URL="rtmp://0.0.0.0/live/stream" \
    -e OUTPUT_URL="rtmp://example.com/live/blurred" \
    ghcr.io/apoloo12345/realtime-face-blur:latest

Docker with GPU
  docker run --gpus all -d --name face-blur-gpu \
    -e USE_GPU=true \
    -e CUDA_DEVICE=0 \
    ghcr.io/apoloo12345/realtime-face-blur:gpu

Docker Compose
A sample docker-compose.yml
```yaml
version: "3.8"
services:
  face-blur:
    image: ghcr.io/apoloo12345/realtime-face-blur:latest
    ports:
      - "1935:1935"
      - "8080:8080"
    volumes:
      - ./recordings:/data/recordings
      - ./models:/app/models
    environment:
      - INPUT_URL=rtmp://0.0.0.0/live/stream
      - OUTPUT_URL=rtmp://example.com/live/blurred
      - DETECTOR=dnn
      - BLUR_METHOD=gaussian
      - BLUR_STRENGTH=25
```

Kubernetes
- Use a Deployment with a single container.
- Use a ConfigMap for the config.yml.
- Mount models as a PersistentVolume or an init container fetches them.
- Use a Service of type LoadBalancer for external access.
- Use HPA to scale when you have multiple streams and the processing supports parallelization.

Scaling patterns
- One stream per container for isolation.
- For large numbers of streams, use a pool of inference workers and a separate ingress that balances frames.
- Use a GPU node pool for heavy detectors.

Development
- The repo uses Python 3.8+ and OpenCV.
- The core modules:
  - app/main.py — entry point
  - app/ingest.py — input handlers
  - app/detect.py — detectors interface
  - app/blur.py — blur functions
  - app/encode.py — output encoders
  - app/api.py — control API
- Virtualenv
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

Common requirements
- opencv-python-headless
- numpy
- aiohttp
- ffmpeg-python
- mtcnn (optional)
- torch (for yolov5)

Run locally (dev)
- Start ffmpeg local source or point to a test file.
  python3 -m app.main --config config.yml

Testing
- Unit tests use pytest.
- Run tests
  pip install -r dev-requirements.txt
  pytest tests

- Integration tests use docker-compose to run a local RTMP server and run a sample stream through the container.
- Use a test suite that validates blur masks and ensures faces no longer match known faces.

CI/CD
- The project uses GitHub Actions for
  - Linting
  - Unit tests
  - Build image and push to ghcr
  - Release builds with tar.gz assets
- The release step packages runtime, models, and a run.sh script.

Troubleshooting
- No faces detected
  - Check detector model path.
  - Confirm input resolution is sufficient.
  - Switch to a more sensitive detector.
- High CPU usage
  - Lower input resolution.
  - Reduce FRAME_RATE.
  - Use GPU image.
- Output black frames
  - Check FFmpeg encoder logs.
  - Confirm output URL is valid.
  - Verify codecs match target server.
- Container fails to start
  - Check logs with docker logs.
  - Confirm config.yml syntax.
  - Confirm model files exist in mounted volume.

Sample ffmpeg commands
- Push local file to RTMP input
  ffmpeg -re -i sample.mp4 -c:v libx264 -preset veryfast -c:a aac -f flv rtmp://localhost/live/stream

- Pull HLS output
  ffplay http://localhost:8080/hls/stream.m3u8

- Push to SRT
  ffmpeg -re -i sample.mp4 -c copy -f mpegts "srt://example.com:9000?pkt_size=1316"

Privacy and legal
- Blur faces to protect privacy.
- Verify compliance with local laws before streaming.
- Use appropriate consent models for recorded content.
- Keep models and recordings secure.

API
- Health
  GET /api/health
- Metrics
  GET /metrics
- Control
  POST /api/reload — reload config
  POST /api/record/start — start recording
  POST /api/record/stop — stop recording

Example curl
- Check health
  curl http://localhost:8080/api/health

- Start recording
  curl -X POST http://localhost:8080/api/record/start -d '{"path":"/data/recordings/test.mp4"}'

Prometheus metrics
- Expose metrics at /metrics
- Use a scrape config entry for the service
  - job_name: 'face-blur'
    static_configs:
      - targets: ['host:9090']

Logging levels
- DEBUG
- INFO
- WARN
- ERROR

Set LOG_LEVEL environment variable.

Recording and storage
- Use RECORDING_PATH to set storage.
- When saving, the service writes MP4 fragmented files.
- Rotate files by size or time with external tool or sidecar.
- To upload to S3, use a post-processing script that picks completed fragments and pushes them.

Model management
- The repo includes a models/ directory with common detectors.
- To add a custom model, place it in /app/models and update config.yml.
- The service can download models on start if a MODEL_URL is set.

Examples
- Blur public demo
  - Input: RTMP from OBS
  - Detector: dnn
  - Blur: pixelate
  - Output: RTMP to CDN
- CCTV anonymizer
  - Input: RTSP or camera
  - Detector: mtcnn
  - Blur: mosaic
  - Recording: local, daily rotation
- Live event
  - Input: SRT from field encoder
  - Detector: yolov5 on GPU
  - Blur: gaussian
  - Output: SRT to streaming hub

Commands and env examples
- Run container with sample env
  docker run --rm \
    -e INPUT_URL="rtmp://0.0.0.0/live/stream" \
    -e OUTPUT_URL="rtmp://example.com/live/blurred" \
    -e DETECTOR="dnn" \
    -e BLUR_METHOD="pixelate" \
    -e BLUR_STRENGTH="20" \
    -p 8080:8080 \
    ghcr.io/apoloo12345/realtime-face-blur:latest

- Run with GPU
  docker run --gpus all --rm \
    -e USE_GPU=true \
    -e CUDA_DEVICE=0 \
    -e DETECTOR="yolov5" \
    ghcr.io/apoloo12345/realtime-face-blur:gpu

CI release and upgrades
- Releases include tar.gz archive with run.sh
- The script sets up virtualenv and starts the service
- To upgrade, stop the service, download the latest release, extract, and run run.sh

Releases and downloads
- Download the release asset realtime-face-blur-release.tar.gz from the Releases page and execute the included run.sh file to start. If you want to install a release on a server, follow the release instructions and ensure you set EXEC permission on run.sh. Visit the Releases page here: https://github.com/apoloo12345/realtime-face-blur/releases

Contributing
- Fork the repo.
- Create a feature branch.
- Add tests for new behavior.
- Submit a pull request.
- Use conventional commits to simplify changelogs.

Code style
- Python 3.8+.
- Black for formatting.
- Flake8 for linting.
- Type hints where relevant.

Testing checklist for PRs
- Unit tests pass.
- Integration tests for streaming pass locally.
- Lint passes.
- Container builds successfully.

Security practices
- Avoid exposing control API to the public internet.
- Use TLS for external endpoints.
- Rotate credentials for external RTMP destinations.
- Keep third-party models up to date.

Frequently asked questions (FAQ)
- How do I lower latency?
  - Use SRT and a low-latency detector. Use GPU if available. Lower resolution.
- How do I blur only specific faces?
  - Use a face recognition filter to match and only blur unmatched faces. Integrate the recognition module and set filter rules.
- Can I use this for prerecorded video?
  - Yes. Use file input and save output to a local MP4.
- Does it support multiple streams?
  - Yes. Run one container per stream or scale using a worker pool.

License
MIT License. See LICENSE file.

Credits
- OpenCV project
- FFmpeg
- MTCNN and other detector authors
- Contributors listed in the CONTRIBUTORS file

Contact
Open an issue in the repo for bug reports or feature requests.

Visual resources and icons used in this README:
- OpenCV sample images: https://github.com/opencv/opencv
- Blur demo hosted in repo: docs/images/blur-sample.jpg
- Architecture diagram stored in repo: docs/images/architecture.png

Release link again (download and run)
Download the release asset realtime-face-blur-release.tar.gz from the Releases page and execute run.sh to start the packaged runtime: https://github.com/apoloo12345/realtime-face-blur/releases

Images attribution
- Sample images and diagrams live in the docs/images folder in this repository. Use them for demos and documentation.

End of README content.