#!/bin/bash

# Stock Investment System - Start Script

echo "=========================================="
echo "  Stock Investment System"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to start backend
start_backend() {
    echo -e "${YELLOW}Starting Backend...${NC}"
    cd "$SCRIPT_DIR/backend"

    # Check venv
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate venv
    source venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt -q

    # Start server
    echo -e "${GREEN}Backend running at http://localhost:8080${NC}"
    python app/api_server.py
}

# Function to start frontend
start_frontend() {
    echo -e "${YELLOW}Starting Frontend...${NC}"
    cd "$SCRIPT_DIR/frontend"

    # Check node_modules
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi

    # Start dev server
    echo -e "${GREEN}Frontend running at http://localhost:3000${NC}"
    npm run dev
}

# Function to start both
start_all() {
    echo -e "${YELLOW}Starting both services...${NC}"

    # Start backend in background
    cd "$SCRIPT_DIR/backend"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt -q
    python app/api_server.py > logs/api.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}Backend running (PID: $BACKEND_PID) at http://localhost:8080${NC}"

    # Start frontend
    cd "$SCRIPT_DIR/frontend"
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev
}

# Main
case "$1" in
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    all)
        start_all
        ;;
    *)
        echo "Usage: $0 {backend|frontend|all}"
        echo ""
        echo "  backend  - Start only the backend API server"
        echo "  frontend - Start only the frontend dev server"
        echo "  all      - Start both services"
        exit 1
        ;;
esac