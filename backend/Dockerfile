# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
# PYTHONUNBUFFERED=1 ensures logs are visible in Cloud Logging
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY rag ./rag
COPY agents ./agents

# Expose the port
EXPOSE 8080

# Command to run the application
# Use the PORT environment variable strictly
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
