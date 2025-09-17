# Use Python 3.11 slim base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create tmp directory for temporary files
RUN mkdir -p /tmp

# Expose Cloud Run default port
EXPOSE 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Start FastAPI app with uvicorn
# (app:app = file app.py / module app.py with FastAPI() object named "app")
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers
