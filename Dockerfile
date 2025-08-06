# Stage 1: Base with OpenCV + CUDA + Dependencies
FROM madtune/opencv-cuda:4.10.0 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    tzdata ffmpeg curl libsm6 libxext6 nginx libnginx-mod-rtmp python3-pip python3-opencv && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: Application Layer
FROM base

WORKDIR /app

# Copy requirements first to leverage caching
COPY requirements.txt ./
# Install only numpy (OpenCV is preinstalled in the base image)
RUN pip install --no-cache-dir -r requirements.txt

# Download OpenCV face detection models (cached unless URLs change)
RUN curl -L -o deploy.prototxt "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt" \
 && curl -L -o res10_300x300_ssd_iter_140000.caffemodel "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"

# Copy only necessary files last to avoid rebuilds on code change
COPY nginx.conf /etc/nginx/nginx.conf
COPY src/main.py ./

# Environment variables
ENV INPUT_URL=srt://remote_host:port?mode=caller
ENV INPUT_WIDTH=1920
ENV INPUT_HEIGHT=1080
ENV INPUT_FPS=30
ENV USE_GPU=0

EXPOSE 1935 8080

CMD ["python3", "main.py"]
