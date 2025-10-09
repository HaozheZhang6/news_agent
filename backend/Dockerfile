# Dockerfile for Voice News Agent Backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions from the repository root for better caching
COPY requirements.txt ./requirements.txt

# Install Python dependencies with hash verification for reproducibility
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# Copy backend application source
COPY backend/ ./

# Create necessary directories
RUN mkdir -p /app/storage/audio /app/storage/logs /app/models

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose default port (Render will set $PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application (use $PORT if provided by Render)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
