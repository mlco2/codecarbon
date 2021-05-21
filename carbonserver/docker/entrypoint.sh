#!/bin/bash
echo "Waiting for database to start..."
sleep 3
echo "Preparing database..."
cd /carbonserver
python3 -m alembic -c carbonserver/database/alembic.ini upgrade head
if [ $? -eq 0 ]; then
    echo "Database ready"
else
    echo "---------------- ERROR initializing database --------------------------"
    exit 1
fi
uvicorn --reload main:app --host 0.0.0.0
