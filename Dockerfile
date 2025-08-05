FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV SRT_URL=srt://0.0.0.0:9000
ENV INPUT_WIDTH=1920
ENV INPUT_HEIGHT=1080
ENV INPUT_FPS=30
# If you set this to 1 make sure to run this image:
# 1. On a machine with NVIDIA Drivers installed
# 2. With GPU support in Docker Desktop enabled: https://docs.docker.com/desktop/features/gpu/
# 3. With "--gpus all" flag
ENV USE_GPU=0

RUN apt-get update && apt-get install -y ffmpeg curl libsm6 libxext6 nginx libnginx-mod-rtmp python3 python3-pip \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
COPY src/main.py ./
RUN pip install --no-cache-dir -r requirements.txt

# Download OpenCV Blurring models
RUN curl -L -o deploy.prototxt "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt" \
  && curl -L -o res10_300x300_ssd_iter_140000.caffemodel "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 1935 8080

CMD ["python3", "main.py"]
