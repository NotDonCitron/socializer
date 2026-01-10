#!/bin/bash

# Start Python API in background
echo "Starting Socializer API..."
cd /app
source venv/bin/activate
uvicorn socializer_api.app:app --host 0.0.0.0 --port 8000 &

# Wait for Python API to be ready (optional, but good practice)
sleep 5

# Start Node.js Admin Panel
echo "Starting Admin Panel..."
cd /app/admin-panel-temp
npm run start
