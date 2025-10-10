# FastAPI Backend Architecture for Voice News Agent

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration management
│   ├── database.py            # Supabase connection
│   ├── cache.py               # Upstash Redis cache
│   ├── models/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── news.py
│   │   ├── conversation.py
│   │   └── stock.py
│   ├── api/                   # API routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── news.py
│   │   ├── voice.py
│   │   ├── conversation.py
│   │   └── user.py
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── news_service.py
│   │   ├── voice_service.py
│   │   ├── ai_service.py
│   │   └── cache_service.py
│   ├── core/                  # Core agent integration
│   │   ├── __init__.py
│   │   ├── agent_wrapper.py   # Wrap existing agent
│   │   ├── voice_processor.py
│   │   └── websocket_manager.py
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── audio_utils.py
│       └── validators.py
├── requirements.txt
├── Dockerfile
├── render.yaml               # Render deployment config
└── README.md
```

## Core API Endpoints

### Authentication & User Management
```python
# POST /api/auth/login
# POST /api/auth/logout  
# GET /api/auth/me
# PUT /api/auth/preferences
```

### News & Content
```python
# GET /api/news/latest?topics=technology,finance&limit=10
# GET /api/news/{news_id}
# POST /api/news/summarize
# GET /api/news/search?q=apple&category=technology
```

### Voice & Conversation
```python
# WebSocket /ws/voice
# POST /api/voice/transcribe
# POST /api/voice/synthesize
# GET /api/conversations/sessions
# GET /api/conversations/{session_id}/messages
```

### Stock & Financial Data
```python
# GET /api/stocks/{symbol}
# GET /api/stocks/watchlist
# POST /api/stocks/watchlist/add
# DELETE /api/stocks/watchlist/{symbol}
```

### Analytics & Insights
```python
# GET /api/analytics/interactions
# GET /api/analytics/preferences
# POST /api/analytics/track
```

## Real-Time Voice Streaming Architecture

**🚀 NEW: Marmadi Real-Time Voice Processing**

We're implementing true real-time voice communication with instant interruption capabilities. See detailed documentation:

- **[design.md](./design.md)** - Complete architecture design and implementation details
- **[marmadi.md](./marmadi.md)** - Project implementation plan and technical specifications

### Key Features
- **Continuous Audio Streaming**: Frontend streams audio chunks to backend
- **Server-Side VAD**: Backend detects voice activity and speech patterns
- **Instant Interruption**: Agent stops immediately when user starts speaking
- **Natural Conversation Flow**: No button pressing required

### Current WebSocket Events

#### Client → Server
```json
{
  "event": "audio_chunk",
  "data": {
    "audio_chunk": "base64_encoded_audio",
    "session_id": "uuid",
    "timestamp": 1234567890
  }
}

{
  "event": "start_session",
  "data": {
    "user_id": "uuid",
    "session_id": "uuid",
    "audio_settings": {...}
  }
}
```

### Server → Client
```json
{
  "event": "transcription",
  "data": {
    "text": "tell me the news",
    "confidence": 0.95,
    "session_id": "uuid",
    "timestamp": 1234567890
  }
}

{
  "event": "agent_response",
  "data": {
    "text": "Here are today's headlines...",
    "news_items": [...],
    "session_id": "uuid"
  }
}

{
  "event": "tts_chunk",
  "data": {
    "audio_chunk": "base64_encoded_audio",
    "chunk_index": 0,
    "session_id": "uuid"
  }
}

{
  "event": "agent_interrupted",
  "data": {
    "session_id": "uuid",
    "reason": "user_speech_detected",
    "timestamp": 1234567890
  }
}
```

## Integration with Existing Agent

### Agent Wrapper Service
```python
class AgentWrapper:
    def __init__(self):
        # Import your existing agent
        from src.agent import NewsAgent
        from src.memory import conversation_memory
        
        self.agent = NewsAgent()
        self.memory = conversation_memory
        
    async def process_voice_command(self, command: str, user_id: str):
        # Process through existing agent
        response = await self.agent.get_response(command)
        
        # Store in database
        await self.store_conversation(user_id, command, response)
        
        return response
```

## Environment Variables for Render
```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Cache
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token

# AI Services
ZHIPUAI_API_KEY=your-key
ALPHAVANTAGE_API_KEY=your-key

# Voice Services
SENSEVOICE_MODEL_PATH=/app/models
EDGE_TTS_VOICE=en-US-AriaNeural

# App Settings
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend.vercel.app
MAX_CONNECTIONS=100
