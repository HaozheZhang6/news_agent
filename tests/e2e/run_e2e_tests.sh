#!/bin/bash
# E2E Test Runner (relocated to tests/e2e)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

resolve_project_root() {
  local dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/pyproject.toml" ] || [ -f "$dir/Makefile" ]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}

PROJECT_ROOT="$(resolve_project_root)"

BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PID=""
FRONTEND_PID=""
BACKEND_LOG="/tmp/e2e_backend.log"
FRONTEND_LOG="/tmp/e2e_frontend.log"

cleanup() {
  echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
  [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
  lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
  lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
  echo -e "${GREEN}✓ Cleanup complete${NC}"
}
trap cleanup EXIT INT TERM

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Voice News Agent - End-to-End Test Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}Checking dependencies...${NC}"
command -v uv >/dev/null 2>&1 || { echo -e "${RED}✗ uv required${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}✗ npm required${NC}"; exit 1; }
echo -e "${GREEN}✓ All dependencies found${NC}\n"

echo -e "${CYAN}Step 1: Starting Backend${NC}"
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
  lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
  sleep 2
fi
cd "$PROJECT_ROOT"
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
for i in {1..30}; do
  if curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then break; fi
  sleep 1
done

echo -e "${CYAN}Step 2: Starting Frontend${NC}"
if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
  lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
  sleep 2
fi
cd "$PROJECT_ROOT/frontend"
npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
for i in {1..60}; do
  if curl -s http://localhost:$FRONTEND_PORT >/dev/null 2>&1; then break; fi
  sleep 1
done

echo -e "${CYAN}Step 3: Running Backend E2E Tests${NC}"
cd "$PROJECT_ROOT"
uv run pytest tests/integration/test_e2e_vad_interruption.py -v -s || exit 1

echo -e "${GREEN}✓ Backend E2E tests passed!${NC}\n"
echo -e "Frontend: http://localhost:$FRONTEND_PORT"
echo -e "Backend:  http://localhost:$BACKEND_PORT"
echo -e "API Docs: http://localhost:$BACKEND_PORT/docs"
echo -e "Health:   http://localhost:$BACKEND_PORT/health\n"

wait $BACKEND_PID $FRONTEND_PID


