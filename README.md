# Voice-Activated News Agent with Smart Memory & Streaming

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/HaozheZhang6/news_agent)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/HaozheZhang6/news_agent)

An advanced voice-activated news recommendation agent with **real-time voice streaming**, **WebSocket API**, and **cloud deployment** capabilities. Built with **FastAPI**, **SenseVoice ASR**, **smart memory systems**, and **streaming TTS** for natural voice interactions across web and mobile platforms.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start-3-5-minutes)
- [Installation Options](#installation-options)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Documentation Index](#documentation-index)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Voice News Agent provides intelligent, context-aware news recommendations through natural voice conversations. The system features dual ASR modes (local SenseVoice vs HuggingFace Space API), real-time WebSocket streaming, and smart memory for contextual interactions.

**Current Status:** Backend MVP complete with streaming WebSocket API, ready for Render deployment and iOS integration.

**Tech Stack:** FastAPI • Supabase • Upstash Redis • SenseVoice ASR • Edge-TTS • GLM-4-Flash

---

## Key Features

### Real-Time Voice Interaction
- **Dual ASR Modes**: Local SenseVoice model (fast, offline) or HuggingFace Space API (lightweight, cloud-ready)
- **Environment-Based Configuration**: Toggle between local/remote ASR with `USE_LOCAL_ASR` flag
- **WebSocket Streaming**: Bidirectional voice communication with chunked TTS responses
- **WebRTC VAD**: Smart voice activity detection with 40% activation threshold
- **Sub-100ms Interruption**: Instant response to voice during TTS playback

### Smart Conversational Memory
- **Context Awareness**: "Tell me more" intelligently refers to recent news items
- **Deep-Dive Detection**: Automatically identifies which news story to elaborate on
- **Topic Tracking**: Remembers conversation topics (technology, finance, politics, crypto)
- **Reference Resolution**: "Explain that", "dive deeper", "what about the first one" work naturally

### Priority-Based Command Processing
- **5-Level Priority System**: Immediate → Refinement → Contextual → Normal → Expired
- **Command Refinement**: "Actually, I meant..." cancels previous commands and prioritizes new intent
- **Time-Based Expiry**: Commands older than 5 seconds get lower priority
- **Smart Interruption**: Context-aware command processing with automatic cleanup

### Audio Compression Pipeline
- **80%+ Bandwidth Reduction**: Modern Opus/WebM compression achieving 5.5x compression ratio
- **Real-Time Processing**: Client-side compression → Base64 encoding → WebSocket transmission
- **WebRTC Standards**: Industry-standard Opus codec for optimal speech quality
- **Streaming TTS**: Chunked audio responses with base64 encoding for smooth playback

### Cloud-Ready Architecture
- **FastAPI Backend**: Async WebSocket + REST API endpoints
- **Supabase PostgreSQL**: User profiles, preferences, conversation history
- **Upstash Redis**: 5-layer caching (news, AI, sessions, voice, stocks)
- **Fast Deployment**: Less than 2 minutes on Render free tier

---

## Quick Start (3-5 Minutes)

### Prerequisites
- Python 3.9+ (3.11 recommended for Render deployment)
- Virtual environment manager (`uv` recommended)
- API keys: ZhipuAI, AlphaVantage, Supabase, Upstash Redis

### Step 1: Clone and Install

```bash
# Clone repository
git clone https://github.com/HaozheZhang6/news_agent.git
cd news_agent

# Install lightweight production dependencies (HF Space ASR only)
uv sync --frozen

# OR install with local ASR support (adds torch, funasr - ~2GB)
uv sync --frozen --extra local-asr
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp env_files/env.example env_files/.env

# Edit with your API keys
# Required: ZHIPUAI_API_KEY, ALPHAVANTAGE_API_KEY, SUPABASE_URL,
#           SUPABASE_KEY, UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN
```

### Step 3: Run the Server

```bash
# Start FastAPI server
make run-server

# OR with HF Space ASR only (like production)
make run-server-hf
```

Access:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **WebSocket Test**: Open `voice_continuous.html` in browser

**That's it!** You're ready to start using the voice agent.

---

## Installation Options

### Option 1: Lightweight (Production/Render)
For deployment or if you prefer cloud ASR:

```bash
uv sync --frozen
```

**What you get:**
- HuggingFace Space API for ASR (no local model needed)
- Edge-TTS for text-to-speech
- Full backend API and WebSocket streaming
- ~500MB install size

### Option 2: Full Installation (Local Development)
For local development with offline ASR:

```bash
uv sync --frozen --extra local-asr
```

**What you get:**
- Local SenseVoice ASR model (fast, offline-capable)
- All production dependencies
- ~2.5GB install size (includes PyTorch)

**Download SenseVoice Model (Optional):**
```bash
uv run python scripts/download_sensevoice.py
```

### Option 3: Development with Testing
For contributors and developers:

```bash
uv sync --frozen --extra local-asr --extra dev --extra test
make install-dev
```

---

## Running the Application

### Backend API Server

```bash
# With local ASR model
make run-server

# With HF Space ASR only (production mode)
make run-server-hf

# Manual start
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Local Voice Agent (Standalone)

```bash
# Start standalone voice agent (no backend needed)
make src

# OR
uv run python -m src.main
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Access frontend at: http://localhost:3000

---

## Testing

### Run All Tests

```bash
make run-tests

# OR specific test suites
make test-backend        # Backend tests only
make test-src           # Source component tests only
make test-integration   # Integration tests only
make test-fast          # Exclude slow tests
```

### Test with Coverage

```bash
make test-coverage
```

### Manual WebSocket Testing

```bash
# Start server
make run-server

# Open browser test client
open voice_continuous.html
```

### Test HuggingFace Space ASR

```bash
make test-hf-space
```

---

## Project Structure

```
News_agent/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── api/                  # REST & WebSocket endpoints
│   │   │   ├── profile.py        # User preferences/watchlist
│   │   │   ├── conversation.py   # Conversation logging
│   │   │   ├── voice.py          # Voice commands
│   │   │   └── websocket.py      # WebSocket streaming
│   │   ├── core/                 # Core business logic
│   │   │   ├── agent_wrapper.py  # Agent integration
│   │   │   ├── streaming_handler.py # TTS streaming
│   │   │   └── websocket_manager.py # Connection management
│   │   ├── models/               # Pydantic models
│   │   ├── config.py             # Environment configuration
│   │   ├── database.py           # Supabase integration
│   │   ├── cache.py              # Upstash Redis caching
│   │   └── main.py               # FastAPI application
│   └── requirements.txt          # Pinned dependencies
│
├── src/                          # Local voice agent (standalone)
│   ├── agent.py                  # News agent logic with GLM-4-Flash
│   ├── voice_input.py            # SenseVoice ASR integration
│   ├── voice_output.py           # TTS & audio playback
│   ├── memory.py                 # Conversation memory system
│   ├── command_queue.py          # Priority command queue
│   └── main.py                   # CLI entry point
│
├── tests/                        # Comprehensive test suite
│   ├── backend/                  # Backend API tests
│   ├── src/                      # Source component tests
│   └── integration/              # End-to-end tests
│
├── docs/                         # Setup documentation
│   ├── LOCAL_SETUP.md            # Detailed local setup guide
│   └── RENDER_DEPLOYMENT.md      # Deployment instructions
│
├── reference/                    # Technical documentation
│   ├── API_DESIGN.md             # API specifications
│   ├── SYSTEM_DESIGN_CURRENT.md  # Architecture overview
│   ├── IMPLEMENTATION_SUMMARY.md # Feature implementation
│   ├── DATABASE_SETUP.md         # Database schema
│   └── [20+ technical guides]    # Detailed references
│
├── env_files/                    # Environment configuration (gitignored)
│   ├── env.example               # Main environment template
│   ├── supabase.env              # Database config
│   ├── upstash.env               # Redis cache config
│   └── render.env                # Deployment config
│
├── database/                     # Database schema & setup
│   ├── schema.sql                # Supabase database schema
│   └── README.md                 # Database documentation
│
├── frontend/                     # React frontend (Next.js)
│   ├── src/
│   │   ├── components/           # UI components
│   │   └── utils/                # Client utilities
│   └── package.json              # Frontend dependencies
│
├── scripts/                      # Utility scripts
│   ├── download_sensevoice.py    # Download ASR model
│   └── test_local_setup.py       # Verify local setup
│
├── render.yaml                   # Render deployment blueprint
├── Makefile                      # Development commands
├── pyproject.toml                # Project metadata (uv)
└── README.md                     # This file
```

---

## Documentation Index

### Getting Started
- **[README.md](README.md)** - This file (quick start, overview)
- **[docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md)** - Detailed local setup guide with troubleshooting
- **[docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md)** - Cloud deployment instructions

### Product & Planning
- **[PRD.md](PRD.md)** - Product Requirements Document
- **[MVP.md](MVP.md)** - MVP status, architecture, deployment guide
- **[TODO.md](TODO.md)** - Task tracker and development roadmap
- **[VERSION.md](VERSION.md)** - Version history and changelog

### Technical Documentation
- **[reference/API_DESIGN.md](reference/API_DESIGN.md)** - REST & WebSocket API specifications
- **[reference/SYSTEM_DESIGN_CURRENT.md](reference/SYSTEM_DESIGN_CURRENT.md)** - System architecture overview
- **[reference/IMPLEMENTATION_SUMMARY.md](reference/IMPLEMENTATION_SUMMARY.md)** - Feature implementation details
- **[reference/DATABASE_SETUP.md](reference/DATABASE_SETUP.md)** - Supabase database schema & setup
- **[reference/STREAMING_AND_DEPLOYMENT.md](reference/STREAMING_AND_DEPLOYMENT.md)** - WebSocket streaming guide

### Specialized Guides
- **[reference/HF_SPACE_MIGRATION_SUMMARY.md](reference/HF_SPACE_MIGRATION_SUMMARY.md)** - HuggingFace Space ASR integration
- **[reference/LATENCY_OPTIMIZATION_GUIDE.md](reference/LATENCY_OPTIMIZATION_GUIDE.md)** - Performance optimization
- **[reference/FRONTEND_LOGGING_GUIDE.md](reference/FRONTEND_LOGGING_GUIDE.md)** - Frontend debugging
- **[reference/CONTINUOUS_VOICE_GUIDE.md](reference/CONTINUOUS_VOICE_GUIDE.md)** - Voice interaction patterns
- **[reference/DOCUMENTATION_INDEX.md](reference/DOCUMENTATION_INDEX.md)** - Complete documentation index

### Deployment & Operations
- **[reference/SENSEVOICE_DEPLOYMENT_SETUP.md](reference/SENSEVOICE_DEPLOYMENT_SETUP.md)** - SenseVoice model deployment
- **[reference/RENDER_DEPLOYMENT_FIX.md](reference/RENDER_DEPLOYMENT_FIX.md)** - Deployment troubleshooting
- **[database/README.md](database/README.md)** - Database operations guide

### Troubleshooting & Fixes
- **[reference/VAD_FIXES.md](reference/VAD_FIXES.md)** - Voice activity detection issues
- **[reference/WEBSOCKET_FIXES.md](reference/WEBSOCKET_FIXES.md)** - WebSocket connection problems
- **[reference/AUDIO_PIPELINE_FIXES.md](reference/AUDIO_PIPELINE_FIXES.md)** - Audio processing issues
- **[reference/FRONTEND_WEBSOCKET_FIX.md](reference/FRONTEND_WEBSOCKET_FIX.md)** - Frontend WebSocket debugging

---

## Deployment

### Render Cloud Deployment (Recommended)

**Deploy in under 2 minutes:**

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - New → Web Service → Connect Repository
   - Select `news_agent` repository

3. **Configure Blueprint**
   - Render will auto-detect `render.yaml`
   - Set environment variables in dashboard:
     - `ZHIPUAI_API_KEY`
     - `ALPHAVANTAGE_API_KEY`
     - `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
     - `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`
     - `USE_LOCAL_ASR=false` (use HF Space API)
     - `HF_SPACE_NAME=hz6666/SenseVoiceSmall`

4. **Deploy!**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - WebSocket streaming and HTTPS included

**Free Tier Includes:**
- 512MB RAM
- WebSocket support
- Auto-scaling
- HTTPS/SSL
- Zero cold start (with background job)

**See [docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md) for detailed instructions.**

### Local Production Mode

```bash
# Simulate production environment locally
make run-server-hf

# This runs with USE_LOCAL_ASR=false (HF Space only)
```

---

## Configuration

### Environment Variables

Create `env_files/.env` with the following:

```bash
# AI Services (Required)
ZHIPUAI_API_KEY=your_zhipuai_key           # GLM-4-Flash LLM
ALPHAVANTAGE_API_KEY=your_alphavantage_key # News & stock data

# Database (Required)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Cache (Required)
UPSTASH_REDIS_REST_URL=your_redis_url
UPSTASH_REDIS_REST_TOKEN=your_redis_token

# ASR Configuration
USE_LOCAL_ASR=true                         # false for cloud/production
HF_SPACE_NAME=hz6666/SenseVoiceSmall      # HuggingFace Space for remote ASR
SENSEVOICE_MODEL_PATH=/path/to/model      # Local model path (optional)

# TTS Configuration
EDGE_TTS_VOICE=en-US-AriaNeural           # Voice for TTS
EDGE_TTS_RATE=1.0                         # Speech rate multiplier

# Optional Services
OPENAI_API_KEY=your_openai_key            # Fallback LLM
NEWS_API_KEY=your_newsapi_key             # Alternative news source
FINNHUB_API_KEY=your_finnhub_key          # Financial data
```

### ASR Mode Selection

**Local ASR (Development):**
```bash
USE_LOCAL_ASR=true
SENSEVOICE_MODEL_PATH=/app/models/SenseVoiceSmall
```
- Fast, offline-capable
- Requires local model download (~1GB)
- Best for development and testing

**Remote ASR (Production):**
```bash
USE_LOCAL_ASR=false
HF_SPACE_NAME=hz6666/SenseVoiceSmall
```
- Lightweight deployment
- No model download needed
- Ideal for Render free tier

### Makefile Commands

```bash
make help           # Show all available commands
make install        # Install production dependencies
make install-dev    # Install dev dependencies + local ASR
make run-server     # Start server with local ASR
make run-server-hf  # Start server with HF Space ASR (production mode)
make src            # Run standalone voice agent
make test-backend   # Run backend tests
make test-coverage  # Run tests with coverage report
make lint           # Check code quality
make format         # Format code with black/isort
make clean          # Clean build artifacts
```

---

## Voice Commands

### General News
- "What's the news?"
- "Tell me what's happening"
- "Latest headlines"

### Topic-Specific News
- "Tell me about technology news"
- "What's happening in finance?"
- "Any news on the economy?"

### Stock Information
- "What's the stock price of Apple?"
- "How much is NVDA?"
- "Tell me about Tesla stock"

### Smart Contextual Commands
- **"Tell me more"** - Refers to recent news items
- **"Dive deeper"** - Context-aware explanations
- **"Explain that"** - Auto-identifies target from conversation
- **"What about the first one"** - References specific news items

### Interruption & Correction
- **"Stop"** - Halt current speech immediately
- **"Actually, I meant..."** - Cancel previous, prioritize new command
- **"No, instead..."** - Smart command refinement
- **"Wait, cancel that"** - Immediate cancellation

### Preference Management
- "Add technology to my preferred topics"
- "Remove politics from my preferred topics"
- "What are my preferred topics?"
- "Add GOOG to my watchlist"
- "Remove MSFT from my watchlist"
- "What's in my watchlist?"

### System Commands
- "Help" - Show available commands
- "Volume up/down" - Audio level control
- "Speak faster/slower" - Speech speed adjustment
- "Exit" / "Quit" - Graceful shutdown

---

## Example Conversation

```
USER: "Tell me the latest news"
AGENT: "Here are today's headlines: 1. Apple announces new AI features..."

USER: "Tell me more about Apple"
AGENT: "Apple's new AI features include enhanced Siri capabilities..."

USER: "Actually, I meant the stock price"
AGENT: "The latest stock price for AAPL is $229.35."

USER: "Add it to my watchlist"
AGENT: "AAPL has been added to your watchlist."
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Voice Input Thread                      │
│   SenseVoice ASR → WebRTC VAD → Command Classification     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Smart Priority Queue                        │
│  IMMEDIATE → REFINEMENT → CONTEXTUAL → NORMAL → EXPIRED    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Memory System (Supabase)                        │
│   Context History • News Items • Topic Tracking             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            Agent Processing (GLM-4-Flash)                    │
│   AlphaVantage API • yfinance • Upstash Cache              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Voice Output Thread (Edge-TTS)                 │
│   Streaming TTS → Audio Playback → Interruption Monitor    │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Threading Architecture**: Lightweight threading for better performance (60% memory reduction vs multiprocessing)
- **WebSocket Streaming**: Real-time bidirectional communication
- **5-Layer Cache**: News, AI responses, sessions, voice, stock data
- **Smart Memory**: Context-aware conversations with deep-dive detection

---

## Performance Metrics

- **Voice Recognition**: 200-500ms (local) / 1-3s (HF Space)
- **Command Classification**: <1ms (dictionary-based)
- **Memory Lookup**: <5ms (context resolution)
- **Interruption Response**: <100ms (voice detection to TTS stop)
- **Queue Processing**: <10ms (command prioritization)

**Resource Usage:**
- **Memory**: 150-300MB (production) / 2-4GB (with local ASR model)
- **CPU**: Moderate during voice processing, low during idle
- **Storage**: Audio logs ~1-5MB per conversation (MP3 compressed)
- **Network**: API calls only for news/stock data (voice processing is local/optional)

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes** and add tests
4. **Run tests**: `make run-tests`
5. **Format code**: `make format`
6. **Commit changes**: Follow conventional commit format (see `.cursor/agent-rules/commit.mdc`)
7. **Push to your fork**: `git push origin feature/your-feature`
8. **Create a Pull Request**

**Development Setup:**
```bash
make install-dev    # Install dev dependencies
make test-backend   # Run backend tests
make test-coverage  # Check coverage
make lint           # Check code quality
```

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

Built with:
- **FastAPI** - Modern Python web framework
- **GLM-4-Flash** - Efficient LLM by ZhipuAI
- **SenseVoice** - Multilingual ASR by Alibaba DAMO Academy
- **Edge-TTS** - Microsoft Edge's text-to-speech
- **Supabase** - PostgreSQL database platform
- **Upstash Redis** - Serverless Redis cache

---

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/HaozheZhang6/news_agent/issues)
- **Documentation**: [docs/](docs/) and [reference/](reference/)
- **Repository**: [https://github.com/HaozheZhang6/news_agent](https://github.com/HaozheZhang6/news_agent)

---

**Built with ❤️ using FastAPI, GLM-4-Flash, SenseVoice ASR, Edge-TTS, Supabase, and Upstash Redis**
