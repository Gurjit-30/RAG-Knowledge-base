# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure data directory exists
RUN mkdir -p /app/data/vector_store /app/data/raw

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the FastAPI application
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
