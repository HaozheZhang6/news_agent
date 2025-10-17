# Voice News Agent Makefile
# Using uv for Python package management

# Use uv for Python package management
ifeq (,$(PYTHON))
ifneq (,$(wildcard .venv/bin/python))
PYTHON := .venv/bin/python
else
PYTHON := $(shell command -v python3 || command -v python)
endif
endif

.PHONY: help install install-dev install-test run-server run-server-hf src run-tests test-backend test-src test-integration test-coverage test-fast clean lint format check-deps setup-env db-apply schema-apply db-seed upstash-test stop-servers

# Default target
help:
	@echo "Voice News Agent - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  init           Initialize uv project (run once)"
	@echo "  install        Install production dependencies (lightweight, for Render)"
	@echo "  install-dev    Install dev dependencies + local ASR (torch, funasr)"
	@echo "  install-test   Install test dependencies with uv"
	@echo "  setup-env      Setup environment files"
	@echo ""
	@echo "Development:"
	@echo "  run-server     Start FastAPI development server (with local ASR model)"
	@echo "  run-server-hf  Start FastAPI development server (HF Space ASR only, like Render)"
	@echo "  run-frontend   Start frontend development server (local backend)"
	@echo "  run-frontend-remote Start frontend development server (remote Render backend)"
	@echo "  src            Start voice agent (runs python -m src.main)"
	@echo "  run-tests      Run all tests"
	@echo "  test-backend   Run backend tests only"
	@echo "  test-src       Run source component tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  test-fast      Run fast tests only (exclude slow tests)"
	@echo "  test-render     Test Render WebSocket deployment"
	@echo "  test-render-sample Test Render with specific sample"
	@echo "  test-render-health Test Render health endpoint only"
	@echo "  test-hf-space   Test Hugging Face Space ASR"
	@echo "  test-hf-space-sample Test HF Space with specific sample"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  check-deps     Check for dependency updates"
	@echo ""
	@echo "Utilities:"
	@echo "  clean          Clean build artifacts and cache"
	@echo "  stop-servers   Stop all running backend and frontend servers"

# Setup environment files
setup-env:
	@echo "Setting up environment files..."
	@cp env_files/env.example backend/.env
	@echo "✅ Environment files created"

# Install dependencies
install:
	@echo "Installing production dependencies with uv..."
	@uv sync --no-dev
	@echo "✅ Production dependencies installed"

install-dev:
	@echo "Installing development dependencies with uv..."
	@uv sync --extra local-asr
	@echo "✅ Development dependencies installed (including local ASR)"

install-test:
	@echo "Installing test dependencies with uv..."
	@uv sync --extra test
	@echo "✅ Test dependencies installed"

# Run development server with local ASR model
run-server:
	@echo "Starting FastAPI development server (with local SenseVoice model)..."
	@echo "Local ASR: ENABLED (USE_LOCAL_ASR=true)"
	@USE_LOCAL_ASR=true uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Run development server with HF Space ASR only (like Render)
run-server-hf:
	@echo "Starting FastAPI development server (HF Space ASR only, no local model)..."
	@echo "Local ASR: DISABLED (USE_LOCAL_ASR=false)"
	@echo "This simulates Render production environment"
	@USE_LOCAL_ASR=false uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Run frontend development server (local backend)
run-frontend:
	@echo "Starting frontend development server (local backend)..."
	@cd frontend && VITE_API_URL=http://localhost:8000 npm run dev

# Run frontend development server (remote Render backend)
run-frontend-remote:
	@echo "Starting frontend development server (remote Render backend)..."
	@echo "Using Render backend: https://voice-news-agent-api.onrender.com"
	@cd frontend && VITE_API_URL=https://voice-news-agent-api.onrender.com npm run dev

# Supabase and Upstash setup helpers (local-only; do not commit secrets)
db-apply:
	@echo "Applying Supabase schema from database/schema.sql..."
	@psql $$DATABASE_URL -f database/schema.sql

schema-apply: db-apply

# Seed demo data (requires DATABASE_URL and DEMO_USER_ID)
db-seed:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is not set"; exit 1; fi
	@if [ -z "$$DEMO_USER_ID" ]; then echo "DEMO_USER_ID is not set"; exit 1; fi
	@echo "Seeding demo data with DEMO_USER_ID=$$DEMO_USER_ID..."
	@psql $$DATABASE_URL -v demo_user_id="$$DEMO_USER_ID" -f database/create_demo_data.sql

upstash-test:
	@echo "Pinging Upstash REST API..."
	@curl -s -H "Authorization: Bearer $$UPSTASH_REDIS_REST_TOKEN" "$$UPSTASH_REDIS_REST_URL/ping" || true

# Merge env_files into backend/.env for local use (no commit)
.PHONY: env-merge
env-merge:
	@echo "Merging env_files/*.env into backend/.env (local only)..."
	@cat env_files/*.env > backend/.env
	@echo "✅ backend/.env updated"

# Run src.main
src:
	@echo "Starting voice-activated news agent (src.main)..."
	@uv run python -m src.main

# Run tests
run-tests:
	@echo "Running all tests..."
	@uv run python tests/run_tests.py

test-backend:
	@echo "Running backend tests..."
	@uv run pytest tests/backend/ -v --tb=short --timeout=15

test-src:
	@echo "Running source component tests..."
	@uv run pytest tests/src/ -v --tb=short --timeout=15

test-integration:
	@echo "Running integration tests..."
	@uv run pytest tests/integration/ -v --tb=short --timeout=15

test-coverage:
	@echo "Running tests with coverage..."
	@uv run pytest tests/ --cov=backend --cov=src --cov-report=html --cov-report=term --timeout=15

test-fast:
	@echo "Running fast tests only..."
	@uv run pytest tests/ -v --tb=short -m "not slow" --timeout=15

test-e2e:
	@echo "Running end-to-end tests (frontend + backend)..."
	@chmod +x tests/e2e/run_e2e_tests.sh
	@tests/e2e/run_e2e_tests.sh

test-vad:
	@echo "Running VAD tests..."
	@python tests/run_vad_tests.py

# Code quality
lint:
	@echo "Running linting checks..."
	@uv run flake8 backend/ src/ tests/ --max-line-length=100 --ignore=E203,W503 || true
	@uv run black --check backend/ src/ tests/ || true
	@uv run isort --check-only backend/ src/ tests/ || true

format:
	@echo "Formatting code..."
	@uv run black backend/ src/ tests/ || true
	@uv run isort backend/ src/ tests/ || true
	@echo "✅ Code formatted"

check-deps:
	@echo "Checking for dependency updates..."
	@uv tree --outdated

# Utilities
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf __pycache__/
	@rm -rf backend/__pycache__/
	@rm -rf src/__pycache__/
	@rm -rf tests/__pycache__/
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@rm -rf *.egg-info/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup completed"

# Stop all running servers
stop-servers:
	@echo "🛑 Stopping all running servers..."
	@lsof -ti :8000 | xargs kill -9 2>/dev/null || echo "No backend server on port 8000"
	@lsof -ti :3000 | xargs kill -9 2>/dev/null || echo "No frontend server on port 3000"
	@pkill -f "uvicorn backend.app.main:app" 2>/dev/null || echo "No uvicorn processes"
	@pkill -f "npm run dev" 2>/dev/null || echo "No npm dev processes"
	@pkill -f "vite" 2>/dev/null || echo "No vite processes"
	@echo "✅ All servers stopped"

# Quick development workflow
dev: install-dev setup-env
	@echo "Development environment ready!"
	@echo "Run 'make run-server' to start the server"
	@echo "Run 'make run-tests' to run tests"

# Production deployment preparation
prod: install setup-env
	@echo "Production environment ready!"
	@echo "Run 'make run-server' to start the server"

# Initialize uv project (run once)
init:
	@echo "Initializing uv project..."
	@uv init --no-readme
	@echo "✅ uv project initialized"

# Test Hugging Face Space
test-hf-space:
	@echo "Testing Hugging Face Space ASR..."
	@uv run python scripts/test_huggingface_space.py --space-url https://huggingface.co/spaces/hz6666/SenseVoiceSmall

test-hf-space-sample:
	@echo "Testing Hugging Face Space with specific sample..."
	@uv run python scripts/test_huggingface_space.py --sample-id analysis_aapl_deeper --space-url https://huggingface.co/spaces/hz6666/SenseVoiceSmall
