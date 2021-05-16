#!/bin/bash
echo "Preparing database..."
cd /carbonserver/carbonserver/database
python3 -m alembic upgrade head
if [ $? -eq 0 ]; then
    echo "Database ready"
else
    echo "---------------- ERROR initializing database --------------------------"
    exit 1
fi
cd /carbonserver
uvicorn --reload main:app --host 0.0.0.0
