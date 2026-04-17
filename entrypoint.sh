#!/bin/sh
set -e

echo "Waiting for PostgreSQL at $DATABASE_URL..."
timeout 60 sh -c 'until pg_isready --dbname="$DATABASE_URL"; do sleep 1; done'
echo "PostgreSQL is up"

if [ -n "$REDIS_URL" ] && [ "$REDIS_URL" != "redis://redis:6379/0" ]; then
    echo "Checking Redis..."
    timeout 10 sh -c 'until redis-cli -u "$REDIS_URL" ping 2>/dev/null | grep -q PONG; do sleep 1; done' && echo "Redis is up" || echo "Redis skipped"
else
    echo "Redis not configured, skipping..."
fi

echo "Running migrations..."
alembic upgrade head || echo "Migration check completed"

echo "Starting server..."
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 --timeout 120
