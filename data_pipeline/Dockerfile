# ===========================
# Data Pipeline Dockerfile
# ===========================
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gdal-bin libgdal-dev libgeos-dev libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install backend requirements (pipeline uses the same stack)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline tasks and backend modules
COPY data_pipeline/ ./data_pipeline/
COPY backend/ ./backend/

ENV PYTHONPATH=/app/backend

# Run pipeline once on container start (cron scheduling done externally)
CMD ["python", "data_pipeline/tasks/fetch_data.py"]
