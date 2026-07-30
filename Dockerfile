# Phase 12.3 (final fix) — Dockerfile for FastAPI backend
# Multi-stage build for smaller production image

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Phase 12.3 fix — cricketiq.db lives in project ROOT, not inside
# backend/, so it was never copied by "COPY backend/ ." above.
# Copy it explicitly into the same /app directory as the app code,
# matching the path SessionLocal expects at runtime.
COPY cricketiq.db .

# Create data directories (faiss_index is already committed via git,
# these mkdir calls are a safety net in case any are missing)
RUN mkdir -p data/faiss_index data/embeddings data/raw data/processed

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]