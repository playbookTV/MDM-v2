#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down all services...${NC}"
    
    # Kill specific processes
    pkill -f "python main.py" 2>/dev/null || true
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    # Kill all child processes of this script
    jobs -p | xargs -r kill 2>/dev/null || true
    
    # Wait a moment for graceful shutdown
    sleep 2
    
    # Force kill if still running
    jobs -p | xargs -r kill -9 2>/dev/null || true
    
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

# Trap CTRL+C and other termination signals
trap cleanup INT TERM EXIT

echo -e "${BLUE}Starting MDM Development Environment${NC}"
echo "======================================"

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo -e "${YELLOW}⚠️  Redis not running. Start it with: redis-server${NC}"
    echo -e "${YELLOW}   Continuing anyway - services may fail...${NC}"
else
    echo -e "${GREEN}✓ Redis is running${NC}"
fi

# Start FastAPI Backend (port 8000)
echo -e "\n${GREEN}Starting FastAPI Backend...${NC}"
cd /Users/leslieisah/MDM/backend
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi
python main.py &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Start Celery Worker
echo -e "\n${GREEN}Starting Celery Worker...${NC}"
cd /Users/leslieisah/MDM/backend
./scripts/start_celery_worker.sh &
CELERY_PID=$!

# Wait for celery to be ready
sleep 3

# Start React Frontend (port 3000 with proxy to 8000)
echo -e "\n${GREEN}Starting React Frontend...${NC}"
cd /Users/leslieisah/MDM/react-app
pnpm run dev --host &
FRONTEND_PID=$!

# Display status
echo -e "\n${BLUE}======================================"
echo -e "All services are starting up..."
echo -e "======================================${NC}"
echo -e "${GREEN}✓ FastAPI Backend:${NC} http://localhost:8000"
echo -e "${GREEN}✓ React Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}✓ API Docs:${NC} http://localhost:8000/docs"
echo -e "${GREEN}✓ Celery Worker:${NC} Processing jobs from Redis queues"
echo -e "\n${YELLOW}Press CTRL+C to stop all services${NC}\n"

# Keep script running and show logs
wait