# Voice News Agent API Documentation

## Platform Architecture Summary

### **Deployment Stack**
- **Frontend**: Next.js on Vercel
- **Backend**: FastAPI on Render
- **Database**: PostgreSQL on Supabase
- **Cache**: Redis on Upstash
- **WebSocket**: Render (FastAPI WebSocket support)

---

## 🗄️ **Database Design (Supabase)**

### **Core Tables**
1. **`users`** - User profiles and subscription tiers
2. **`user_preferences`** - Voice settings, topics, watchlists
3. **`news_sources`** - News source reliability and categories
4. **`news_articles`** - News content with sentiment analysis
5. **`stock_data`** - Real-time stock prices and metrics
6. **`conversation_sessions`** - User conversation sessions
7. **`conversation_messages`** - Individual messages and audio
8. **`user_interactions`** - Analytics and user behavior
9. **`ai_response_cache`** - Cached AI responses for performance

### **Key Features**
- **Row Level Security (RLS)** - User data isolation
- **Full-text search** - News article search
- **JSONB fields** - Flexible preferences and metadata
- **Triggers** - Automatic timestamp updates
- **Indexes** - Optimized for common queries

---

## 🚀 **API Design (FastAPI)**

### **Authentication Endpoints**
```http
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
PUT  /api/auth/preferences
```

### **News Endpoints**
```http
GET  /api/news/latest?topics=tech,finance&limit=10
GET  /api/news/{news_id}
POST /api/news/summarize
GET  /api/news/search?q=apple&category=technology
GET  /api/news/breaking
```

### **Voice & Conversation Endpoints**
```http
WebSocket /ws/voice
POST /api/voice/transcribe
POST /api/voice/synthesize
GET  /api/conversations/sessions
GET  /api/conversations/{session_id}/messages
POST /api/conversations/{session_id}/interrupt
```

### **Stock & Financial Endpoints**
```http
GET  /api/stocks/{symbol}
GET  /api/stocks/watchlist
POST /api/stocks/watchlist/add
DELETE /api/stocks/watchlist/{symbol}
GET  /api/stocks/market-summary
```

### **User Management Endpoints**
```http
GET  /api/user/preferences
PUT  /api/user/preferences
GET  /api/user/topics
POST /api/user/topics/add
DELETE /api/user/topics/{topic}
GET  /api/user/analytics
```

---

## 🔄 **WebSocket Events (with Audio Compression)**

### **Audio Compression Pipeline**
- **Frontend**: Real-time Opus/WebM compression → Base64 encoding
- **Backend**: Base64 decode → FFmpeg conversion → ASR → LLM → TTS → Base64 encoding
- **Bandwidth Reduction**: 80%+ reduction with 5.5x compression ratio
- **Supported Formats**: Opus, WebM, AAC, MP3, WAV

### **Client → Server Events**
```json
{
  "event": "start_listening",
  "data": {
    "user_id": "uuid",
    "session_id": "uuid",
    "audio_settings": {
      "sample_rate": 16000,
      "channels": 1,
      "format": "pcm"
    }
  }
}

{
  "event": "voice_data",
  "data": {
    "audio_chunk": "base64_encoded_compressed_audio",
    "format": "opus",
    "is_final": true,
    "session_id": "uuid",
    "user_id": "uuid",
    "sample_rate": 16000,
    "file_size": 11667,
    "compression": {
      "codec": "opus",
      "original_size": 64590,
      "compressed_size": 11667,
      "compression_ratio": 5.5,
      "bitrate": 64000
    },
    "timestamp": "2024-01-01T00:00:00Z"
  }
}

{
  "event": "voice_command",
  "data": {
    "command": "tell me the news",
    "session_id": "uuid",
    "confidence": 0.95
  }
}

{
  "event": "interrupt",
  "data": {
    "session_id": "uuid",
    "reason": "user_interruption"
  }
}
```

### **Server → Client Events**
```json
{
  "event": "transcription",
  "data": {
    "text": "tell me the news",
    "confidence": 0.95,
    "session_id": "uuid",
    "processing_time_ms": 150
  }
}

{
  "event": "voice_response",
  "data": {
    "text": "Here are today's headlines...",
    "audio_url": "https://cdn.example.com/audio/response.mp3",
    "news_items": [
      {
        "id": "uuid",
        "title": "Apple announces new AI features",
        "summary": "Apple unveiled new AI capabilities...",
        "topic": "technology",
        "sentiment": 0.8
      }
    ],
    "session_id": "uuid",
    "response_time_ms": 1200
  }
}

{
  "event": "voice_interrupted",
  "data": {
    "session_id": "uuid",
    "reason": "user_interruption",
    "interruption_time_ms": 85
  }
}

{
  "event": "error",
  "data": {
    "error_type": "transcription_failed",
    "message": "Could not process audio",
    "session_id": "uuid"
  }
}
```

---

## 💾 **Cache Strategy (Upstash Redis)**

### **Cache Layers**
1. **News Cache** (15 min TTL)
   - `news:latest:{topics}:{limit}`
   - `news:article:{article_id}`
   - `news:summary:{article_id}:{type}`

2. **AI Response Cache** (1 hour TTL)
   - `ai:response:{prompt_hash}`
   - `ai:summary:{content_hash}`
   - `ai:sentiment:{text_hash}`

3. **User Session Cache** (5 min TTL)
   - `user:session:{user_id}`
   - `user:preferences:{user_id}`
   - `user:conversation:{session_id}`

4. **Voice Cache** (5 min TTL)
   - `voice:audio:{session_id}:{timestamp}`
   - `voice:transcription:{audio_hash}`
   - `voice:tts:{text_hash}:{voice}`

5. **Stock Data Cache** (1 min TTL)
   - `stock:price:{symbol}`
   - `stock:watchlist:{user_id}`
   - `stock:analysis:{symbol}:{period}`

---

## 🔧 **Implementation Plan**

### **Phase 1: Core Backend (Week 1)**
1. **Setup FastAPI project structure**
2. **Configure Supabase connection**
3. **Setup Upstash Redis cache**
4. **Create basic API endpoints**
5. **Implement WebSocket support**

### **Phase 2: Agent Integration (Week 2)**
1. **Wrap existing NewsAgent in FastAPI service**
2. **Implement voice processing pipeline**
3. **Add real-time interruption handling**
4. **Create conversation management**
5. **Add user preference management**

### **Phase 3: Frontend Integration (Week 3)**
1. **Connect Next.js frontend to API**
2. **Implement WebSocket client**
3. **Add voice interaction UI**
4. **Create news display components**
5. **Add conversation history**

### **Phase 4: Deployment & Testing (Week 4)**
1. **Deploy backend to Render**
2. **Deploy frontend to Vercel**
3. **Configure Supabase database**
4. **Setup Upstash Redis**
5. **End-to-end testing**

---

## 📊 **Performance Targets**

### **Response Times**
- **Voice Recognition**: <500ms
- **News Fetching**: <200ms (cached)
- **AI Response**: <2s (cached), <5s (uncached)
- **WebSocket Latency**: <50ms
- **Interruption Response**: <100ms

### **Scalability**
- **Concurrent Users**: 100+ (free tier)
- **WebSocket Connections**: 50+ per instance
- **API Requests**: 1000+ per minute
- **Cache Hit Rate**: >80%

---

## 🔐 **Security Considerations**

### **Authentication**
- **Supabase Auth** - JWT tokens
- **Row Level Security** - Database-level access control
- **API Rate Limiting** - Prevent abuse

### **Data Protection**
- **Audio Data** - Temporary storage, auto-deletion
- **User Preferences** - Encrypted storage
- **API Keys** - Environment variables only

### **CORS Configuration**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 **Deployment Configuration**

### **Render Backend Configuration**
```yaml
# render.yaml
services:
  - type: web
    name: voice-news-agent-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: UPSTASH_REDIS_REST_URL
        sync: false
      - key: UPSTASH_REDIS_REST_TOKEN
        sync: false
      - key: ZHIPUAI_API_KEY
        sync: false
      - key: ALPHAVANTAGE_API_KEY
        sync: false
```

### **Vercel Frontend Configuration**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://your-backend.onrender.com",
    "NEXT_PUBLIC_WS_URL": "wss://your-backend.onrender.com"
  }
}
```

This architecture provides a robust, scalable foundation for your voice news agent with excellent performance characteristics and cost-effective deployment on free tiers.
