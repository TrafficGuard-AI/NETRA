# NETRA backend — Hugging Face Spaces (Docker SDK).
# HF free tier gives 16GB RAM / 2 vCPU, so the full torch + YOLO + TrOCR
# pipeline fits comfortably (unlike a 512MB host). HF serves on port 7860.
FROM python:3.11-slim

# OpenCV runtime libs (opencv-python-headless still needs libGL / glib).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces run containers as uid 1000. Create a matching user and point all
# model/caches at writable paths it owns.
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    YOLO_CONFIG_DIR=/home/user/.config/Ultralytics \
    PYTHONUNBUFFERED=1

# The app writes data/ under BASE_DIR (=/app), so /app must be user-owned.
RUN mkdir -p /app && chown -R user:user /app
USER user
WORKDIR /app

# Install deps first for layer caching (CPU torch via the index in requirements).
COPY --chown=user:user backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --user -r backend/requirements.txt

# App code (ultimate_edge_preprocessor.py already lives inside backend/).
COPY --chown=user:user backend/ ./backend/

# Run from backend/ so `app.main` and `ultimate_edge_preprocessor` import cleanly.
WORKDIR /app/backend
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
