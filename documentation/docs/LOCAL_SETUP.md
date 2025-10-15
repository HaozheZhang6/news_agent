# Local Development Setup Guide

**Complete guide for setting up Voice News Agent on your local machine**

Last Updated: 2025-10-14
Version: Backend v0.2.1

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Options](#installation-options)
3. [Quick Start](#quick-start)
4. [SenseVoice Model Setup](#sensevoice-model-setup)
5. [Environment Configuration](#environment-configuration)
6. [Running the Application](#running-the-application)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2+ cores
- RAM: 4GB
- Storage: 10GB free space
- OS: macOS, Linux, or Windows (WSL2)

**Recommended (with local ASR):**
- CPU: 4+ cores
- RAM: 8GB
- Storage: 15GB free space (for SenseVoice model)
- OS: macOS or Linux

### Software Requirements

1. **Python 3.9+** (3.11 recommended)
   ```bash
   python --version
   # Should show: Python 3.9.x or higher
   ```

2. **uv** (Fast Python package manager)
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Verify installation
   uv --version
   ```

3. **Git**
   ```bash
   git --version
   ```

4. **Node.js 18+** (for frontend)
   ```bash
   node --version
   npm --version
   ```

### API Keys Required

| Service | Purpose | Get Key From |
|---------|---------|--------------|
| Supabase | Database | https://supabase.com |
| Upstash Redis | Cache | https://upstash.com |
| ZhipuAI | LLM | https://open.bigmodel.cn |
| HuggingFace | ASR API (optional) | https://huggingface.co/settings/tokens |
| AlphaVantage | News data (optional) | https://alphavantage.co |

---

## Installation Options

You have two installation options depending on whether you want local ASR:

### Option 1: Lightweight (HuggingFace Space ASR Only)

**Best for:**
- Quick testing
- Limited disk space
- Don't need offline capability
- Similar to production environment

**Dependencies:** ~500MB

```bash
git clone https://github.com/HaozheZhang6/news_agent.git
cd news_agent
uv sync --frozen
```

### Option 2: Full (With Local SenseVoice ASR)

**Best for:**
- Fast, offline transcription
- Full development environment
- Testing local ASR features
- Avoiding API rate limits

**Dependencies:** ~2.5GB (includes PyTorch, FunASR)

```bash
git clone https://github.com/HaozheZhang6/news_agent.git
cd news_agent
uv sync --frozen --extra local-asr
# Or use: make install-dev
```

### Comparison

| Feature | Lightweight | Full (Local ASR) |
|---------|-------------|------------------|
| Install size | ~500MB | ~2.5GB |
| Install time | ~2 min | ~5-10 min |
| ASR source | HuggingFace Space API | Local SenseVoice model |
| Offline mode | ❌ No | ✅ Yes |
| Transcription speed | ~1-2s (API latency) | ~0.5s (local) |
| GPU required | ❌ No | Optional (faster) |

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/HaozheZhang6/news_agent.git
cd news_agent
```

### 2. Install Dependencies

**Choose one:**

```bash
# Lightweight (recommended for first time)
uv sync --frozen

# OR Full with local ASR
uv sync --frozen --extra local-asr
```

### 3. Configure Environment

```bash
# Copy example environment file
cp env_files/env.example backend/.env

# Edit with your API keys
nano backend/.env  # or use your favorite editor
```

**Minimal configuration (required):**
```bash
# backend/.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbG...
UPSTASH_REDIS_REST_URL=https://...upstash.io
UPSTASH_REDIS_REST_TOKEN=...
ZHIPUAI_API_KEY=...

# For lightweight setup (no local model)
USE_LOCAL_ASR=false
HF_TOKEN=hf_...

# For full setup (with local model)
USE_LOCAL_ASR=true
```

### 4. Download SenseVoice Model (Full Setup Only)

If you installed with `--extra local-asr`:

```bash
# Download SenseVoice model (~1GB)
uv run python scripts/download_sensevoice.py

# Verify model location
ls -lh models/iic/SenseVoiceSmall/
# Should show: model.pt, config.yaml, etc.
```

### 5. Start Backend

```bash
# Lightweight mode (HF Space ASR)
USE_LOCAL_ASR=false make run-server-hf

# OR Full mode (Local ASR)
USE_LOCAL_ASR=true make run-server

# Server starts at: http://localhost:8000
```

### 6. Start Frontend (Optional)

```bash
cd frontend
npm install
npm run dev

# Frontend starts at: http://localhost:3000
```

### 7. Test

```bash
# Check backend health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs
```

---

## SenseVoice Model Setup

### Understanding SenseVoice Location

The SenseVoice model is stored locally for fast, offline ASR:

```
news_agent/
├── models/
│   └── iic/
│       └── SenseVoiceSmall/          ← Model directory
│           ├── model.pt              ← Main model (~1GB)
│           ├── config.yaml           ← Model config
│           ├── chn_jpn_yue_eng_ko_spectok.bpe.model
│           └── ...
```

### Download Methods

#### Method 1: Automatic (Recommended)

```bash
# Uses ModelScope API
uv run python scripts/download_sensevoice.py

# Downloads to: models/iic/SenseVoiceSmall/
# Time: ~5-10 minutes (depends on connection)
```

#### Method 2: Manual Download

```bash
# 1. Create directory
mkdir -p models/iic/SenseVoiceSmall

# 2. Download from ModelScope
# Visit: https://modelscope.cn/models/iic/SenseVoiceSmall
# Download all files to: models/iic/SenseVoiceSmall/

# 3. Verify files
ls models/iic/SenseVoiceSmall/
# Should show: model.pt, config.yaml, etc.
```

### Verify Installation

```bash
# Check model files
python << EOF
import os
model_path = "models/iic/SenseVoiceSmall"
if os.path.exists(model_path):
    files = os.listdir(model_path)
    print(f"✅ Model found with {len(files)} files")
    print(f"Files: {files}")
else:
    print(f"❌ Model not found at {model_path}")
EOF
```

### Model Location Configuration

The model path is configured in `backend/app/config.py`:

```python
# Default path (relative to project root)
SENSEVOICE_MODEL_PATH = "models/iic/SenseVoiceSmall"

# Or set via environment variable
export SENSEVOICE_MODEL_PATH="/custom/path/to/SenseVoiceSmall"
```

### Storage Requirements

- **Model size**: ~1GB
- **Cache during download**: ~500MB temporary
- **Total needed**: ~1.5GB free space

---

## Environment Configuration

### Environment Files Structure

```
news_agent/
├── env_files/              ← Template files (committed to git)
│   ├── env.example        ← Main template
│   ├── supabase.env       ← Supabase config
│   ├── upstash.env        ← Redis config
│   └── render.env         ← Deployment config
└── backend/
    └── .env               ← Actual config (DO NOT COMMIT)
```

### Complete Configuration

Create `backend/.env` with all required variables:

```bash
# =============================================================================
# ENVIRONMENT
# =============================================================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# =============================================================================
# DATABASE (Supabase)
# =============================================================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# =============================================================================
# CACHE (Upstash Redis)
# =============================================================================
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token-here

# =============================================================================
# VOICE SERVICES
# =============================================================================
# Local ASR (set to true if you have SenseVoice model downloaded)
USE_LOCAL_ASR=true

# HuggingFace Space API (fallback or primary when USE_LOCAL_ASR=false)
HF_TOKEN=hf_your_token_here
HF_SPACE_NAME=hz6666/SenseVoiceSmall

# SenseVoice model path (optional, defaults to models/iic/SenseVoiceSmall)
SENSEVOICE_MODEL_PATH=models/iic/SenseVoiceSmall

# Edge-TTS settings
EDGE_TTS_VOICE=en-US-AriaNeural
EDGE_TTS_RATE=1.0
EDGE_TTS_PITCH=1.0

# =============================================================================
# AI SERVICES
# =============================================================================
# ZhipuAI (GLM-4-Flash LLM)
ZHIPUAI_API_KEY=your-zhipuai-api-key

# Optional: OpenAI (fallback LLM)
OPENAI_API_KEY=sk-your-openai-api-key

# =============================================================================
# NEWS & FINANCIAL DATA
# =============================================================================
# AlphaVantage (stock data)
ALPHAVANTAGE_API_KEY=your-alphavantage-api-key

# Optional: News API
NEWS_API_KEY=your-news-api-key

# Optional: Finnhub
FINNHUB_API_KEY=your-finnhub-api-key

# =============================================================================
# APPLICATION CONFIG
# =============================================================================
HOST=0.0.0.0
PORT=8000
WORKERS=1
SECRET_KEY=your-secret-key-change-this-in-production

# CORS
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
CORS_CREDENTIALS=true

# =============================================================================
# WEBSOCKET CONFIG
# =============================================================================
MAX_WEBSOCKET_CONNECTIONS=50
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_TIMEOUT=300

# =============================================================================
# CACHE CONFIG
# =============================================================================
CACHE_DEFAULT_TTL_SECONDS=900
CACHE_PREFIX=voice_news_agent

# =============================================================================
# RATE LIMITING
# =============================================================================
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

### Minimal Configuration (Quick Test)

For quick testing, you only need:

```bash
# backend/.env (minimal)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token
ZHIPUAI_API_KEY=your-api-key
USE_LOCAL_ASR=false
HF_TOKEN=hf_your_token
```

---

## Running the Application

### Backend Modes

#### Mode 1: HuggingFace Space ASR (Lightweight)

```bash
# Start server with HF Space ASR only
USE_LOCAL_ASR=false make run-server-hf

# Or directly:
USE_LOCAL_ASR=false uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Console output:**
```
Starting FastAPI development server (HF Space ASR only, no local model)...
Local ASR: DISABLED (USE_LOCAL_ASR=false)
This simulates Render production environment
INFO: Uvicorn running on http://0.0.0.0:8000
```

#### Mode 2: Local SenseVoice ASR (Full)

```bash
# Start server with local SenseVoice model
USE_LOCAL_ASR=true make run-server

# Or directly:
USE_LOCAL_ASR=true uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Console output:**
```
Starting FastAPI development server (with local SenseVoice model)...
Local ASR: ENABLED (USE_LOCAL_ASR=true)
🔄 Loading SenseVoice model from models/iic/SenseVoiceSmall...
✅ SenseVoice model loaded successfully
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:3000

### Original Voice Agent (Terminal-Based)

```bash
# Standalone voice agent (no backend needed)
make src

# Or directly:
uv run python src/main.py
```

---

## Testing

### 1. Backend Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed

# Liveness
curl http://localhost:8000/live
```

### 2. API Documentation

Open in browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. WebSocket Connection

```bash
# Install wscat
npm install -g wscat

# Test WebSocket
wscat -c ws://localhost:8000/ws/voice?user_id=test-user

# Should show:
Connected (press CTRL+C to quit)
> {"event":"connected", ...}
```

### 4. Voice Transcription Test

```bash
# Run comprehensive backend tests
make test-backend

# Or specific WebSocket tests
uv run pytest tests/backend/test_websocket.py -v
```

### 5. Audio Pipeline Test

```bash
# Test audio upload and transcription
python test_audio_pipeline.py
```

---

## Troubleshooting

### Common Issues

#### 1. Model Not Found

**Error:**
```
⚠️ SenseVoice model not found at models/iic/SenseVoiceSmall
```

**Solution:**
```bash
# Download model
uv run python scripts/download_sensevoice.py

# Or set USE_LOCAL_ASR=false to use HF Space
USE_LOCAL_ASR=false make run-server-hf
```

#### 2. FunASR Import Error

**Error:**
```
ModuleNotFoundError: No module named 'funasr'
```

**Solution:**
```bash
# Install with local-asr dependencies
uv sync --extra local-asr

# Or use lightweight mode
uv sync
USE_LOCAL_ASR=false make run-server-hf
```

#### 3. Port Already in Use

**Error:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**
```bash
# Stop existing server
make stop-servers

# Or manually:
lsof -ti :8000 | xargs kill -9
```

#### 4. Database Connection Failed

**Error:**
```
WARNING: Database initialization failed
```

**Solution:**
```bash
# 1. Verify Supabase URL and keys
echo $SUPABASE_URL

# 2. Test connection
psql $SUPABASE_URL

# 3. Check database schema
psql $SUPABASE_URL -f database/schema.sql
```

#### 5. Redis Connection Failed

**Error:**
```
WARNING: Cache initialization failed
```

**Solution:**
```bash
# Test Upstash connection
curl -s -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN" \
  "$UPSTASH_REDIS_REST_URL/ping"

# Should return: {"result":"PONG"}
```

#### 6. HuggingFace Space Timeout

**Error:**
```
RuntimeError: HF Space ASR failed and local ASR is disabled
```

**Solution:**
```bash
# 1. Verify HF token
echo $HF_TOKEN

# 2. Test HF Space
curl https://huggingface.co/spaces/hz6666/SenseVoiceSmall

# 3. Use local ASR instead
USE_LOCAL_ASR=true make run-server
```

### Performance Issues

#### Slow Model Loading

```bash
# SenseVoice model takes ~10-30 seconds to load on first start
# This is normal. Subsequent starts are faster.

# To speed up:
# 1. Use SSD (not HDD)
# 2. Ensure 8GB+ RAM available
# 3. Close other applications
```

#### High Memory Usage

```bash
# With local ASR: 2-3GB RAM is normal
# Without local ASR: <500MB RAM is normal

# Monitor memory:
ps aux | grep uvicorn
```

### Development Tips

```bash
# Hot reload for code changes
# uvicorn --reload automatically restarts on code changes

# View logs in real-time
tail -f logs/app.log

# Test with different log levels
LOG_LEVEL=DEBUG make run-server

# Profile performance
uv run python -m cProfile -o profile.stats backend/app/main.py
```

---

## Directory Structure

```
news_agent/
├── backend/                # Backend API
│   ├── app/
│   │   ├── main.py        # FastAPI entry point
│   │   ├── config.py      # Configuration
│   │   ├── core/          # Core services
│   │   │   ├── websocket_manager.py
│   │   │   ├── streaming_handler.py
│   │   │   └── hf_space_asr.py
│   │   └── api/           # API routes
│   └── .env               # Environment variables (create this)
├── frontend/              # React frontend
│   ├── src/
│   └── package.json
├── models/                # Local models
│   └── iic/
│       └── SenseVoiceSmall/  # SenseVoice ASR model
├── database/              # Database schemas
│   └── schema.sql
├── tests/                 # Test suite
├── scripts/               # Utility scripts
│   └── download_sensevoice.py
├── docs/                  # Documentation
├── pyproject.toml         # Python dependencies
├── Makefile              # Development commands
└── README.md             # Project overview
```

---

## Next Steps

After successful setup:

1. **Explore API**: http://localhost:8000/docs
2. **Test Frontend**: http://localhost:3000
3. **Run Tests**: `make test-backend`
4. **Read Docs**: See `docs/` directory
5. **Deploy**: See `docs/RENDER_DEPLOYMENT.md`

---

## Resources

- **Project Repo**: https://github.com/HaozheZhang6/news_agent
- **Documentation**: `docs/` directory
- **Issues**: https://github.com/HaozheZhang6/news_agent/issues
- **SenseVoice**: https://github.com/FunAudioLLM/SenseVoice
- **FastAPI**: https://fastapi.tiangolo.com

---

**Setup Time:**
- Lightweight: ~5 minutes
- Full (with model): ~15 minutes

**Happy Coding! 🚀**
