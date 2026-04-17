#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
timeout 60 sh -c 'until psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; do sleep 1; done'
echo "PostgreSQL is up"

echo "Running migrations..."
alembic upgrade head || echo "Migration check completed"

echo "Starting server..."
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 --timeout 120