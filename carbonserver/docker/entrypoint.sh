#!/bin/bash
set -e
echo "Starting entrypoint script..."
echo "Waiting for database to start..."
python3 <<'PY'
import os
import sys
import time

url = os.environ.get("DATABASE_URL", "")
if not url:
    print("DATABASE_URL not set, skipping DB wait")
    sys.exit(0)

try:
    from sqlalchemy import create_engine, text
except ImportError:
    time.sleep(5)
    sys.exit(0)

engine = create_engine(url, pool_pre_ping=True)
for attempt in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"Database ready after {attempt}s")
        sys.exit(0)
    except Exception:
        time.sleep(1)

print("Database not ready after 30s")
sys.exit(1)
PY
echo "Preparing database..."
cd /carbonserver
echo "Current directory: $(pwd)"
echo "Running alembic upgrade head..."
if python3 -m alembic -c carbonserver/database/alembic.ini current 2>/dev/null | grep -q "(head)"; then
    echo "Database schema already at head, skipping migration"
else
    python3 -m alembic -c carbonserver/database/alembic.ini upgrade head
fi
if [ $? -eq 0 ]; then
    echo "Database ready"
else
    echo "---------------- ERROR initializing database --------------------------"
    exit 1
fi
echo "Starting uvicorn server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*
