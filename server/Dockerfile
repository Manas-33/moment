# Moment server image (Django web + Celery worker share this image).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System deps: ffmpeg (trim/format/mux), node (yt-dlp signature solving for YouTube
# downloads), and the shared libs OpenCV needs at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        nodejs \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

# Default command is the web server; the worker overrides this in docker-compose.
CMD ["gunicorn", "shorts_generator.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--timeout", "300", "--workers", "2"]
