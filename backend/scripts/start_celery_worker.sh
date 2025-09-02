#!/bin/bash

# Modomo Celery Worker Startup Script
# Starts workers that consume from all required queues

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Kill any existing workers
echo "Stopping existing Celery workers..."
pkill -f "celery.*worker" || true
sleep 2

# Start Celery worker with all queues
echo "Starting Celery worker with all queues..."
celery -A app.worker.celery_app worker \
    --loglevel=info \
    --queues=celery,huggingface,dataset_processing,scene_processing,maintenance \
    --concurrency=2 \
    --max-tasks-per-child=100 \
    --heartbeat-interval=30 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat-check

echo "Celery worker started successfully!"