#!/bin/bash
set -e

echo "══════════════════════════════════════════════"
echo "  SF Portal Backend — Production Startup"
echo "══════════════════════════════════════════════"

# ── 1. Run Alembic migrations ──────────────────────────
echo "▶ Running database migrations..."
alembic upgrade head
echo "✅ Migrations applied successfully."

# ── 2. Start Gunicorn with Uvicorn workers ─────────────
echo "▶ Starting Gunicorn (Uvicorn workers)..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${GUNICORN_WORKERS:-2}" \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
