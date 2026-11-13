#!/bin/bash
set -e
echo "Starting entrypoint script..."
echo "Waiting for database to start..."
sleep 5
echo "Preparing database..."
cd /carbonserver
echo "Current directory: $(pwd)"
echo "Listing files in /carbonserver:"
ls -la
echo "Running alembic upgrade head..."
python3 -m alembic -c carbonserver/database/alembic.ini upgrade head
if [ $? -eq 0 ]; then
    echo "Database ready"
else
    echo "---------------- ERROR initializing database --------------------------"
    exit 1
fi
echo "Starting uvicorn server..."
# uvicorn --reload main:app --host 0.0.0.0 --port 8000
# ponytail: --forwarded-allow-ips=* trusts X-Forwarded-For from any peer, so
# request.client.host (used e.g. by the telemetry rate limiter) can be
# spoofed by the caller unless a real reverse proxy always overwrites that
# header first. Kept as-is (maintainer decision); tighten to the proxy's
# actual IP/CIDR if that stops being guaranteed.
uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*
