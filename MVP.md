# 🚀 Voice News Agent - MVP Documentation

**Version:** 3.0 (Cloud MVP)  
**Status:** Backend complete, pending deployment  
**Last Updated:** 2025-10-09

---

## 📋 Table of Contents

1. [MVP Overview](#mvp-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Features](#features)
5. [Setup & Installation](#setup--installation)
6. [Deployment](#deployment)
7. [Testing](#testing)
8. [API Documentation](#api-documentation)
9. [Roadmap](#roadmap)

---

## 🎯 MVP Overview

### What We Built

A **cloud-native voice news agent** with:
- Real-time WebSocket streaming for voice communication
- FastAPI backend with async processing
- Supabase PostgreSQL for data persistence
- Upstash Redis for high-performance caching
- Streaming TTS with chunked audio delivery
- iOS-ready API for client-side ASR integration

### MVP Goals

✅ **Achieved:**
- Hands-free news consumption via voice
- Context-aware conversations with memory
- Real-time audio streaming (low latency)
- Cloud deployment (Render-ready)
- Scalable architecture (free tier → production)

⏳ **Pending:**
- Production deployment on Render
- iOS app integration
- User authentication
- Multi-user support

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐
│   iOS/Web App   │
│  (Client-side)  │
│   ASR + Audio   │
└────────┬────────┘
         │ WebSocket
         │ (wss://...)
         ▼
┌─────────────────────────────────┐
│   FastAPI Backend (Render)      │
│  ┌───────────────────────────┐  │
│  │  WebSocket Manager         │  │
│  │  - Streaming Handler       │  │
│  │  - Agent Wrapper           │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  REST API Endpoints        │  │
│  │  - News API                │  │
│  │  - User API                │  │
│  │  - Conversation API        │  │
│  └───────────────────────────┘  │
└────────┬────────────┬───────────┘
         │            │
         ▼            ▼
┌─────────────┐  ┌───────────┐
│  Supabase   │  │  Upstash  │
│  PostgreSQL │  │   Redis   │
│  (Database) │  │  (Cache)  │
└─────────────┘  └───────────┘
         │
         ▼
┌──────────────────────┐
│  External APIs       │
│  - ZhipuAI (LLM)     │
│  - AlphaVantage      │
│  - yfinance          │
│  - Edge-TTS          │
└──────────────────────┘
```

### Data Flow

**Voice Command Flow:**
```
1. Client (iOS/Web)
   └→ Transcribe audio (client-side ASR)
   └→ Send text via WebSocket: {event: "voice_command", data: {...}}

2. Backend
   └→ Receive command
   └→ Check cache (Redis)
   └→ If miss: Process with agent (GLM-4-Flash)
   └→ Fetch news (AlphaVantage/yfinance)
   └→ Store in DB (Supabase)
   └→ Generate TTS (edge-tts)
   └→ Stream audio chunks back

3. Client
   └→ Receive: {event: "tts_chunk", data: {audio_chunk: "..."}}
   └→ Play audio chunks in real-time
   └→ Display text response
```

---

## 🛠️ Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | FastAPI 0.104+ | Async WebSocket + REST API |
| **Runtime** | Python 3.10+ | Backend language |
| **Package Manager** | uv | Fast dependency management |
| **WebSocket** | FastAPI WebSocket | Real-time communication |
| **Async** | asyncio + uvicorn | Concurrent request handling |

### Data Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | Supabase PostgreSQL | User data, conversations, news |
| **Cache** | Upstash Redis | 5-layer caching system |
| **ORM** | SQLAlchemy 2.0+ | Database abstraction |
| **Migrations** | Alembic | Schema versioning |

### AI & Voice
| Component | Technology | Purpose |
|-----------|------------|---------|
| **LLM** | GLM-4-Flash (ZhipuAI) | Conversation & summarization |
| **TTS** | Edge-TTS | Streaming text-to-speech |
| **ASR** | iOS Speech Framework | Client-side voice recognition |
| **Voice Fallback** | SenseVoice/Whisper | Server-side ASR (optional) |

### External APIs
| Service | Purpose | Free Tier |
|---------|---------|-----------|
| **AlphaVantage** | News sentiment + stock data | 25 requests/day |
| **yfinance** | Stock prices | Unlimited |
| **ZhipuAI** | LLM responses | Pay-as-you-go |
| **Edge-TTS** | Text-to-speech | Unlimited |

### DevOps
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Deployment** | Render | Cloud hosting |
| **Containerization** | Docker | Consistent environments |
| **CI/CD** | GitHub Actions (future) | Automated deployment |
| **Monitoring** | Render Metrics | Performance tracking |

---

## ✨ Features

### Core Features (MVP)

#### 1. Voice Interaction ✅
- **WebSocket Streaming**: Real-time bidirectional communication
- **Chunked TTS**: Audio streamed in 4KB chunks for low latency
- **Partial Transcriptions**: Real-time ASR feedback
- **Interruption Support**: Cancel commands mid-execution

#### 2. News Intelligence ✅
- **Multi-source Aggregation**: AlphaVantage + yfinance
- **Topic Detection**: Technology, finance, politics, crypto, energy
- **Smart Summarization**: AI-powered news rephrasing for voice
- **Breaking News**: Real-time alerts

#### 3. Conversation Memory ✅
- **Context Tracking**: Remember last 10 exchanges
- **Deep-dive Detection**: "Tell me more" refers to recent news
- **Topic Awareness**: Track conversation themes
- **Reference Resolution**: "Explain that" works naturally

#### 4. User Preferences ✅
- **Topic Interests**: Save preferred news topics
- **Stock Watchlist**: Track favorite stocks
- **Voice Settings**: Speed, volume preferences
- **Notification Settings**: Alert preferences

#### 5. Data Persistence ✅
- **Supabase Integration**: All data persisted in PostgreSQL
- **Conversation History**: Full conversation logs
- **User Profiles**: Persistent user accounts
- **Analytics Tracking**: Usage metrics

#### 6. Caching System ✅
- **5-Layer Cache**:
  1. News cache (15 min TTL)
  2. AI response cache (1 hour TTL)
  3. User session cache (5 min TTL)
  4. Voice cache (5 min TTL)
  5. Stock data cache (1 min TTL)

### Advanced Features (Future)

- [ ] User authentication (JWT)
- [ ] Push notifications
- [ ] Multi-user support
- [ ] Social sharing
- [ ] Podcast integration
- [ ] Video summaries

---

## 🚀 Setup & Installation

### Prerequisites

- **Python**: 3.9 or higher
- **uv**: Package manager ([install](https://github.com/astral-sh/uv))
- **Docker**: For local testing (optional)
- **Git**: Version control

### API Keys Required

1. **ZhipuAI API Key** - For LLM (GLM-4-Flash)
   - Sign up: https://open.bigmodel.cn/
   - Free tier: Limited requests

2. **AlphaVantage API Key** - For news & stock data
   - Sign up: https://www.alphavantage.co/support/#api-key
   - Free tier: 25 requests/day

3. **Supabase** - PostgreSQL database
   - Create project: https://supabase.com/
   - Free tier: 500MB database

4. **Upstash Redis** - Cache
   - Create database: https://upstash.com/
   - Free tier: 10K commands/day

### Local Setup

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/News_agent.git
cd News_agent

# 2. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# 3. Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 4. Install dependencies
uv pip install -r backend/requirements.txt
uv pip install -r tests/requirements-test.txt

# 5. Configure environment
# Create env_files/supabase.env
echo "SUPABASE_URL=https://your-project.supabase.co" > env_files/supabase.env
echo "SUPABASE_KEY=your-anon-key" >> env_files/supabase.env
echo "SUPABASE_SERVICE_KEY=your-service-role-key" >> env_files/supabase.env

# Create env_files/upstash.env
echo "UPSTASH_REDIS_REST_URL=https://your-db.upstash.io" > env_files/upstash.env
echo "UPSTASH_REDIS_REST_TOKEN=your-token" >> env_files/upstash.env

# 6. Apply Supabase schema
# Option A: Use Supabase SQL Editor
# Copy contents of database/schema.sql and run in Supabase dashboard

# Option B: Use MCP Supabase tool (if available)
# Schema already applied in development

# 7. Run backend server
make run-server

# Or manually:
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Verify Installation

```bash
# Check server health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","services":{"database":"healthy","cache":"healthy","websocket":"healthy"}}

# Open WebSocket test client
open test_websocket.html
```

---

## 🌐 Deployment

### Render Deployment (Recommended)

#### Prerequisites
- GitHub account
- Render account (free tier)
- Environment variables ready

#### Step 1: Prepare Repository

```bash
# Ensure render.yaml is at repo root
ls render.yaml  # Should exist

# Commit all changes
git add -A
git commit -m "Deploy: Backend MVP v3.0"
git push origin main
```

#### Step 2: Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Select `render.yaml`
5. Review service configuration
6. Click "Apply"

#### Step 3: Set Environment Variables

In Render dashboard, set these variables:

**Required:**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
UPSTASH_REDIS_REST_URL=https://your-db.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token
ZHIPUAI_API_KEY=your-zhipuai-key
ALPHAVANTAGE_API_KEY=your-alphavantage-key
SECRET_KEY=generate-a-random-secret-key
```

**Optional:**
```
CORS_ORIGINS=["https://your-frontend.vercel.app","http://localhost:3000"]
MAX_WEBSOCKET_CONNECTIONS=10
LOG_LEVEL=INFO
```

#### Step 4: Deploy

1. Render will auto-deploy when you push to main
2. Wait 3-5 minutes for deployment
3. Check logs for errors
4. Visit your app URL: `https://your-app.onrender.com`

#### Step 5: Verify Deployment

```bash
# Check health
curl https://your-app.onrender.com/health

# Test WebSocket (use Postman or websocat)
wss://your-app.onrender.com/ws/voice?user_id=test
```

### Docker Deployment (Alternative)

```bash
# Build Docker image
cd backend
docker build -t voice-news-agent:latest .

# Run container
docker run -d -p 8000:8000 \
  --env-file ../env_files/supabase.env \
  --env-file ../env_files/upstash.env \
  voice-news-agent:latest

# Check logs
docker logs -f <container_id>
```

---

## 🧪 Testing

### Local Testing

**1. Backend API:**
```bash
# Start server
make run-server

# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

**2. WebSocket Streaming:**
```bash
# Open test client
open test_websocket.html

# Or use Postman WebSocket
# URL: ws://localhost:8000/ws/voice?user_id=test
```

**3. Run Test Suite:**
```bash
# All tests
make run-tests

# Backend tests only
make test-backend

# Fast tests (skip slow ones)
make test-fast
```

### Manual Test Checklist

- [ ] Server starts without errors
- [ ] Health endpoint returns "healthy"
- [ ] WebSocket connection succeeds
- [ ] Voice command triggers response
- [ ] TTS chunks stream back
- [ ] Partial transcriptions work
- [ ] Interruption works
- [ ] Session cleanup on disconnect
- [ ] Supabase data persists
- [ ] Redis cache works

### Production Testing

```bash
# Replace with your Render URL
export API_URL="https://your-app.onrender.com"

# Health check
curl $API_URL/health

# WebSocket test (use websocat)
websocat wss://your-app.onrender.com/ws/voice?user_id=prod_test
```

---

## 📖 API Documentation

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API docs |
| `/api/news/latest` | GET | Get latest news |
| `/api/news/search` | GET | Search news |
| `/api/news/topics` | GET | List topics |
| `/api/user/preferences` | GET/PUT | User preferences |
| `/ws/voice` | WebSocket | Voice streaming |

### WebSocket Events

**Client → Server:**
- `voice_command` - Send voice command text
- `voice_data` - Send audio chunk (base64)
- `interrupt` - Cancel current operation
- `start_listening` / `stop_listening` - Control listening

**Server → Client:**
- `connected` - Connection established
- `transcription` - Command acknowledged
- `voice_response` - Text response
- `tts_chunk` - Audio chunk (streaming)
- `streaming_complete` - Stream finished
- `partial_transcription` - Partial ASR result
- `audio_received` - Audio buffered
- `error` - Error occurred

**Example: Send Voice Command**
```json
{
  "event": "voice_command",
  "data": {
    "session_id": "session-uuid",
    "command": "latest tech news",
    "confidence": 0.95
  }
}
```

**Example: Receive TTS Chunk**
```json
{
  "event": "tts_chunk",
  "data": {
    "audio_chunk": "BASE64_ENCODED_AUDIO",
    "chunk_index": 0,
    "format": "mp3",
    "session_id": "session-uuid"
  }
}
```

See [VOICE_INPUT_TESTING.md](VOICE_INPUT_TESTING.md) for detailed examples.

---

## 🗺️ Roadmap

### Phase 1: Backend MVP ✅ (Current)
- [x] FastAPI backend
- [x] WebSocket streaming
- [x] Supabase integration
- [x] Upstash Redis caching
- [x] Streaming TTS
- [x] Docker deployment config
- [x] Test suite
- [ ] Render deployment (pending manual test)

### Phase 2: iOS App (Next)
- [ ] SwiftUI interface
- [ ] Speech Framework ASR
- [ ] WebSocket client
- [ ] Audio playback
- [ ] Conversation history UI
- [ ] Settings screen
- [ ] App Store submission

### Phase 3: Features & Polish
- [ ] User authentication
- [ ] Push notifications
- [ ] Multi-user support
- [ ] Enhanced caching
- [ ] Performance optimization
- [ ] Analytics dashboard

### Phase 4: Platform Expansion
- [ ] Android app
- [ ] Web app (Next.js)
- [ ] Desktop app
- [ ] Voice assistant integrations

### Phase 5: Enterprise
- [ ] API licensing
- [ ] White-label solution
- [ ] Team accounts
- [ ] Advanced analytics
- [ ] Custom integrations

---

## 📊 Success Metrics

### MVP Success Criteria

**Technical:**
- [ ] Server uptime > 99%
- [ ] WebSocket connection success rate > 95%
- [ ] Average response time < 2s
- [ ] TTS streaming latency < 500ms
- [ ] Zero critical security vulnerabilities

**User:**
- [ ] 10+ beta testers
- [ ] Average session duration > 5 min
- [ ] User retention > 40% (7-day)
- [ ] NPS score > 50

**Business:**
- [ ] $0 hosting cost (free tier)
- [ ] iOS app published
- [ ] 100+ downloads
- [ ] 5+ positive reviews

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon) for guidelines.

**Quick Start:**
1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit PR

---

## 📞 Support & Contact

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: [Your email]
- **Documentation**: See `/docs` folder

---

**Built with ❤️ using FastAPI, Supabase, Upstash, GLM-4-Flash, and Edge-TTS**

