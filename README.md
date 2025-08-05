# Realtime Face Blur with Docker

This project provides a Dockerized solution for real-time face blurring in video streams using OpenCV and FFmpeg. It includes an integrated NGINX-RTMP server to serve the processed video stream. The application supports both CPU and NVIDIA GPU acceleration for face detection and processing.

## Features

- **Real-time face blurring**: Detects and blurs faces in video streams.
- **Multiple input support**: Accepts Secure Reliable Transport (SRT), RTMP, HTTP and HTTPS streams as input.
- **RTMP output**: Streams the processed video to an RTMP server.
- **GPU acceleration**: Optional NVIDIA GPU support for faster face detection.
- **Integrated NGINX-RTMP server**: Serves the processed stream locally.

## Prerequisites

- Docker installed on your system.
- NVIDIA GPU (optional) with drivers installed and Docker GPU support enabled.
- OBS or any RTMP-compatible client to view the processed stream.

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd realtime-face-blur
```

### 2. Build the Docker Image

```bash
docker-compose build
```

### 3. Run the Application

```bash
docker-compose up
```

### 4. View the Processed Stream

Access the processed stream at:

```
rtmp://<host>:1935/live/blurred
```

You can use OBS or any RTMP-compatible client to view the stream.

## Environment Variables

The following environment variables can be configured in the `docker-compose.yml` file:

| Variable       | Default Value         | Description                                                                 |
|----------------|-----------------------|-----------------------------------------------------------------------------|
| `INPUT_URL`      | `srt://remote_host:port?mode=caller` | Input Source. Can be SRT (default mode caller), rtmp, http or https.                                                      |
| `INPUT_WIDTH`  | `1920`               | Width of the input video stream.                                           |
| `INPUT_HEIGHT` | `1080`               | Height of the input video stream.                                          |
| `INPUT_FPS`    | `30`                 | Frames per second of the input video stream.                               |
| `USE_GPU`      | `0`                  | Set to `1` to enable NVIDIA GPU acceleration (requires GPU support).       |

## File Structure

```
.
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile           # Dockerfile for building the image
├── nginx.conf           # NGINX configuration for RTMP server
├── requirements.txt     # Python dependencies
└── src/
    └── main.py          # Main Python script for face blurring
```

## Notes

- If GPU support is enabled, ensure that:
  1. NVIDIA drivers are installed on the host machine.
  2. Docker Desktop GPU support is enabled.
  3. The container is run with the `--gpus all` flag.

- The OpenCV face detection model files (`deploy.prototxt` and `res10_300x300_ssd_iter_140000.caffemodel`) are downloaded during the Docker build process.

## Troubleshooting

- **SRT stream not connecting**: Ensure the SRT URL is correct and the input stream is active.
- **GPU not detected**: Verify that NVIDIA drivers are installed and Docker GPU support is enabled.
- **RTMP stream not accessible**: Check that the NGINX server is running and the ports are correctly mapped.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
```