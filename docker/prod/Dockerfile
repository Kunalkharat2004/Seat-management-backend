# ──────────────────────────────────────────────────────────
# Production Multi-Stage Dockerfile for SF Portal Backend
# Usage: podman build -f docker/prod/Dockerfile ..
# ──────────────────────────────────────────────────────────

# ─── Stage 1: Builder ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies for compiled packages (psycopg2, bcrypt, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Stage 2: Production ────────────────────────────────
FROM python:3.12-slim AS production

# Install only runtime dependencies (libpq for psycopg2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Copy entrypoint script
COPY docker/prod/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start via entrypoint (runs migrations + gunicorn)
ENTRYPOINT ["/app/entrypoint.sh"]
