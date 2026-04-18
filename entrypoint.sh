#!/bin/sh
set -e

echo "=== CHUDO AI Production Startup ==="

echo "Waiting for PostgreSQL..."
timeout 90 sh -c '
  until psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; do
    echo "PostgreSQL unavailable - retrying in 2s..."
    sleep 2
  done
'
echo "PostgreSQL is up"

echo "Running Alembic migrations..."
alembic upgrade head

if [ -n "$REDIS_URL" ]; then
  echo "Checking Redis..."
  timeout 10 sh -c '
    until redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; do
      sleep 1
    done
  ' && echo "Redis ready" || echo "Redis unavailable (continuing)"
else
  echo "Redis not configured"
fi

echo "Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 120 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  -b "0.0.0.0:${PORT:-8000}"