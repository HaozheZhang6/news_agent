#!/bin/bash
# End-to-End Test Runner for Voice News Agent
# Runs both backend and frontend together for full integration testing

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PID=""
FRONTEND_PID=""
BACKEND_LOG="/tmp/e2e_backend.log"
FRONTEND_LOG="/tmp/e2e_frontend.log"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"

    if [ ! -z "$BACKEND_PID" ]; then
        echo "  Stopping backend (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null || true
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        echo "  Stopping frontend (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    # Kill any remaining processes on these ports
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true

    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Set up trap to cleanup on exit
trap cleanup EXIT INT TERM

# Print header
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Voice News Agent - End-to-End Test Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"

# Check if required commands exist
echo -e "${CYAN}Checking dependencies...${NC}"
command -v uv >/dev/null 2>&1 || { echo -e "${RED}✗ uv is required but not installed${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}✗ npm is required but not installed${NC}"; exit 1; }
echo -e "${GREEN}✓ All dependencies found${NC}\n"

# Step 1: Start Backend
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Step 1: Starting Backend Server${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if backend is already running
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Backend already running on port $BACKEND_PORT${NC}"
    echo -e "${YELLOW}  Killing existing process...${NC}"
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo "  Starting backend on port $BACKEND_PORT..."
echo "  Logs: $BACKEND_LOG"

cd "$PROJECT_ROOT"
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo "  Backend PID: $BACKEND_PID"

# Wait for backend to start
echo -n "  Waiting for backend to be ready"
for i in {1..30}; do
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓ Backend is ready!${NC}\n"
        break
    fi
    echo -n "."
    sleep 1

    # Check if backend process died
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "\n${RED}✗ Backend failed to start. Check logs: $BACKEND_LOG${NC}"
        tail -20 "$BACKEND_LOG"
        exit 1
    fi

    if [ $i -eq 30 ]; then
        echo -e "\n${RED}✗ Backend failed to start within 30 seconds${NC}"
        echo "Last 20 lines of log:"
        tail -20 "$BACKEND_LOG"
        exit 1
    fi
done

# Step 2: Start Frontend
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Step 2: Starting Frontend Server${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if frontend is already running
if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Frontend already running on port $FRONTEND_PORT${NC}"
    echo -e "${YELLOW}  Killing existing process...${NC}"
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo "  Starting frontend on port $FRONTEND_PORT..."
echo "  Logs: $FRONTEND_LOG"

cd "$PROJECT_ROOT/frontend"
npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

echo "  Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
echo -n "  Waiting for frontend to be ready"
for i in {1..60}; do
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓ Frontend is ready!${NC}\n"
        break
    fi
    echo -n "."
    sleep 1

    # Check if frontend process died
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "\n${RED}✗ Frontend failed to start. Check logs: $FRONTEND_LOG${NC}"
        tail -20 "$FRONTEND_LOG"
        exit 1
    fi

    if [ $i -eq 60 ]; then
        echo -e "\n${RED}✗ Frontend failed to start within 60 seconds${NC}"
        echo "Last 20 lines of log:"
        tail -20 "$FRONTEND_LOG"
        exit 1
    fi
done

# Step 3: Run Backend Tests
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Step 3: Running Backend E2E Tests${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

uv run pytest tests/integration/test_e2e_vad_interruption.py -v -s || {
    echo -e "\n${RED}✗ Backend E2E tests failed${NC}"
    exit 1
}

echo -e "\n${GREEN}✓ Backend E2E tests passed!${NC}\n"

# Step 4: Display URLs for Manual Testing
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Step 4: Manual Testing${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${GREEN}Both servers are running!${NC}"
echo ""
echo -e "  ${BLUE}Frontend:${NC} http://localhost:$FRONTEND_PORT"
echo -e "  ${BLUE}Backend:${NC}  http://localhost:$BACKEND_PORT"
echo -e "  ${BLUE}API Docs:${NC} http://localhost:$BACKEND_PORT/docs"
echo -e "  ${BLUE}Health:${NC}   http://localhost:$BACKEND_PORT/health"
echo ""
echo -e "${YELLOW}Manual Test Checklist:${NC}"
echo "  1. Open frontend in browser"
echo "  2. Click the microphone button"
echo "  3. Speak a question (e.g., 'What is the price of Apple?')"
echo "  4. Wait for agent response"
echo "  5. While agent is speaking, interrupt by speaking again"
echo "  6. Verify agent stops and processes your interruption"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  Backend:  tail -f $BACKEND_LOG"
echo "  Frontend: tail -f $FRONTEND_LOG"
echo ""
echo -e "${CYAN}Press Ctrl+C to stop servers and exit${NC}\n"

# Keep script running until interrupted
wait $BACKEND_PID $FRONTEND_PID
