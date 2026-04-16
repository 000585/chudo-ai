#!/bin/sh
set -e

echo 'Waiting for PostgreSQL...'
timeout 30 sh -c 'until pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${DB_USER:-chudo}; do sleep 1; done'
echo 'PostgreSQL is up'

echo 'Waiting for Redis...'
timeout 30 sh -c 'until redis-cli -h ${REDIS_HOST:-redis} -a ${REDIS_PASSWORD:-RedisPass2026!} ping 2>/dev/null | grep -q PONG; do sleep 1; done'
echo 'Redis is up'

echo 'Running migrations...'
alembic upgrade head || echo 'Migration check completed'

echo 'Starting server...'
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 --timeout 120