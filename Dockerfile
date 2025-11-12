# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (for psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application code
COPY . .

# Default environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose Flask/Gunicorn port
EXPOSE 5001

# Start Gunicorn in production mode
CMD ["gunicorn", "-b", "0.0.0.0:5001", "app:app"]
