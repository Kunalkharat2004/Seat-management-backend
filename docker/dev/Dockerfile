# ──────────────────────────────────────────────────────────
# Development Dockerfile for SF Portal Backend
# Usage: podman build -f docker/dev/Dockerfile ..
# ──────────────────────────────────────────────────────────

# Base image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI with uvicorn (hot-reload for dev)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
