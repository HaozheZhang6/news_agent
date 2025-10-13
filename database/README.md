# 📊 Voice News Agent - Database Documentation

## Overview

This directory contains database documentation and SQL scripts for the Voice News Agent system. The database uses **PostgreSQL via Supabase** with a simplified schema optimized for voice interactions and news delivery.

**Database URL**: https://app.supabase.com/project/zaipmdlbcraufolrizpn  
**Schema Status**: 4 tables active (35% of planned schema)  
**Last Updated**: 2025-10-12

---

## 📋 Database Tables Overview

| Table | Rows | Columns | Purpose | Status |
|-------|------|---------|---------|--------|
| [`users`](#users) | 1 | 8 | User accounts & preferences | ✅ Active |
| [`conversation_sessions`](#conversation_sessions) | 1 | 6 | Voice session tracking | ✅ Active |
| [`conversation_messages`](#conversation_messages) | 0 | 8 | Chat history & messages | ✅ Ready |
| [`news_articles`](#news_articles) | 0 | 6 | Cached news content | ✅ Ready |

**Total**: 4 tables, 28 columns

---

## 🔹 Table: `users`

**Purpose**: Core user account information and personalized preferences

### Schema
```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY,                    -- References auth.users(id)
    email TEXT UNIQUE NOT NULL,             -- User email address
    preferred_topics TEXT[] DEFAULT '{}',   -- News topics of interest
    watchlist_stocks TEXT[] DEFAULT '{}',   -- Stock symbols to track
    subscription_tier TEXT DEFAULT 'free',  -- 'free', 'premium', 'enterprise'
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- Account creation time
    updated_at TIMESTAMPTZ DEFAULT NOW(),   -- Last profile update
    last_active TIMESTAMPTZ DEFAULT NOW()   -- Last user activity
);
```

### Column Details

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | UUID | Primary key, links to Supabase Auth | `03f6b167-0c4d-4983-a380-54b8eb42f830` |
| `email` | TEXT | Unique email for authentication | `demo@voicenews.test` |
| `preferred_topics` | TEXT[] | News categories user follows | `['tech', 'finance', 'crypto']` |
| `watchlist_stocks` | TEXT[] | Stock tickers user tracks | `['TSLA', 'AAPL', 'NVDA']` |
| `subscription_tier` | TEXT | Account level (free/premium/enterprise) | `'free'` |
| `created_at` | TIMESTAMPTZ | When account was created | `2025-10-10T08:23:57+00:00` |
| `updated_at` | TIMESTAMPTZ | Last profile modification (auto-updated) | `2025-10-10T08:26:05+00:00` |
| `last_active` | TIMESTAMPTZ | Last login/API call/voice interaction | `2025-10-10T08:23:57+00:00` |

### Usage
- **Authentication**: Links to Supabase Auth system
- **Personalization**: `preferred_topics` filters news feed
- **Stock Tracking**: `watchlist_stocks` drives price alerts
- **Billing**: `subscription_tier` controls feature access

### Sample Data
```sql
INSERT INTO users VALUES (
    '03f6b167-0c4d-4983-a380-54b8eb42f830',
    'demo@voicenews.test',
    ARRAY['tech', 'finance'],
    ARRAY['TSLA', 'AAPL'],
    'free',
    NOW(),
    NOW(),
    NOW()
);
```

---

## 🔹 Table: `conversation_sessions`

**Purpose**: Tracks voice conversation sessions between users and the AI agent

### Schema
```sql
CREATE TABLE public.conversation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMPTZ DEFAULT NOW(),
    session_end TIMESTAMPTZ,                    -- NULL while active
    topics_discussed TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true
);
```

### Column Details

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | UUID | Unique session identifier | `03bf84b1-b7d9-470d-8809-5a57e1e1b6e2` |
| `user_id` | UUID | Foreign key to users table | `03f6b167-0c4d-4983-a380-54b8eb42f830` |
| `session_start` | TIMESTAMPTZ | When WebSocket connected | `2025-10-12T08:18:13+00:00` |
| `session_end` | TIMESTAMPTZ | When WebSocket disconnected (NULL if active) | `NULL` |
| `topics_discussed` | TEXT[] | Topics covered in conversation | `['stock prices', 'tech news']` |
| `is_active` | BOOLEAN | TRUE if WebSocket still connected | `true` |

### Usage
- **WebSocket Tracking**: Each connection creates a new session
- **Analytics**: Track conversation duration and topics
- **History**: Link messages to specific sessions
- **Active Sessions**: Find currently connected users

### Lifecycle
1. **Start**: WebSocket connects → new session created
2. **Active**: User interacts → `topics_discussed` updated
3. **End**: WebSocket disconnects → `session_end` set, `is_active` = false

---

## 🔹 Table: `conversation_messages`

**Purpose**: Individual messages within conversation sessions (user inputs, agent responses, system events)

### Schema
```sql
CREATE TABLE public.conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,                      -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,                   -- Message text
    referenced_news_ids UUID[] DEFAULT '{}', -- News articles mentioned
    metadata JSONB DEFAULT '{}',             -- Flexible additional data
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Column Details

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | UUID | Unique message identifier | Auto-generated |
| `session_id` | UUID | Parent conversation session | Links to `conversation_sessions.id` |
| `user_id` | UUID | Message owner | Links to `users.id` |
| `role` | TEXT | Message type: 'user', 'assistant', 'system' | `'user'` |
| `content` | TEXT | Message text content | `"What's the price of TSLA?"` |
| `referenced_news_ids` | UUID[] | News articles cited in message | `[uuid1, uuid2]` |
| `metadata` | JSONB | Additional data (ASR confidence, processing time) | `{"confidence": 0.95}` |
| `created_at` | TIMESTAMPTZ | Message timestamp | `2025-10-12T08:20:15+00:00` |

### Message Types (role)

| Role | Description | Content Example |
|------|-------------|-----------------|
| `user` | Transcribed user speech | `"Tell me about Tesla stock"` |
| `assistant` | AI agent response | `"Tesla (TSLA) is currently trading at $245.27..."` |
| `system` | System events/status | `"WebSocket connected"` |

### Metadata Examples
```json
{
  "asr_model": "whisper-1",
  "confidence_score": 0.95,
  "processing_time_ms": 1250,
  "tts_voice": "en-US-AriaNeural",
  "interrupted": false
}
```

### Usage
- **Conversation History**: Complete record of all interactions
- **Quality Monitoring**: Track ASR confidence and processing times
- **Context**: Link messages to news articles discussed
- **Analytics**: Understand user behavior and preferences

---

## 🔹 Table: `news_articles`

**Purpose**: Cached news articles fetched from external APIs with basic metadata

### Schema
```sql
CREATE TABLE public.news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,                     -- Article headline
    summary TEXT,                            -- Brief excerpt
    url TEXT,                               -- Link to original article
    published_at TIMESTAMPTZ NOT NULL,      -- When article was published
    created_at TIMESTAMPTZ DEFAULT NOW()    -- When cached in our DB
);
```

### Column Details

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | UUID | Unique article identifier | Auto-generated |
| `title` | TEXT | Article headline (required) | `"Tesla Reports Record Q3 Earnings"` |
| `summary` | TEXT | Brief excerpt or first paragraph | `"Tesla Inc. reported record quarterly earnings..."` |
| `url` | TEXT | Link to original article | `"https://reuters.com/business/tesla-earnings"` |
| `published_at` | TIMESTAMPTZ | When source published article | `2025-10-11T14:30:00+00:00` |
| `created_at` | TIMESTAMPTZ | When we cached the article | `2025-10-11T15:00:00+00:00` |

### Usage
- **News Cache**: Store articles from AlphaVantage, RSS feeds
- **Voice Responses**: Provide article summaries in conversations
- **Deduplication**: Prevent importing same article twice
- **Freshness**: Track when articles were published vs cached

### Data Sources
- AlphaVantage News API
- RSS feeds from major news outlets
- Financial news aggregators
- Tech news sources

### Sample Data
```sql
INSERT INTO news_articles VALUES (
    uuid_generate_v4(),
    'Tesla Stock Surges on Strong Q3 Results',
    'Tesla Inc. shares jumped 8% in after-hours trading following better-than-expected quarterly earnings...',
    'https://example.com/tesla-earnings',
    '2025-10-11 14:30:00+00:00',
    NOW()
);
```

---

## 🔧 Database Configuration

### Extensions
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- Text search
```

### Row Level Security (RLS)
- **Enabled** on user-related tables (`users`, `conversation_sessions`, `conversation_messages`)
- **Public read** on content tables (`news_articles`)
- **Current Issue**: Backend uses service_role key (bypasses RLS)
- **Recommended**: Use anon key with proper policies

### Indexes
```sql
-- Conversation queries
CREATE INDEX idx_conversation_messages_session ON conversation_messages(session_id);
CREATE INDEX idx_conversation_messages_user ON conversation_messages(user_id);
CREATE INDEX idx_conversation_sessions_user ON conversation_sessions(user_id);

-- News queries
CREATE INDEX idx_news_articles_published ON news_articles(published_at DESC);
CREATE INDEX idx_news_articles_title ON news_articles USING GIN(to_tsvector('english', title));
```

---

## 📁 Files in This Directory

### SQL Scripts
| File | Purpose | Status |
|------|---------|--------|
| `schema.sql` | Complete schema definition (planned) | ⚠️ Doesn't match actual |
| `create_demo_data.sql` | Sample data for testing | ✅ Ready |

### Documentation
| File | Purpose |
|------|---------|
| `README.md` | This file - complete database documentation |

### Python Tools (in `.cursor/`)
| Tool | Purpose | Usage |
|------|---------|-------|
| `supabase_tool.py` | Database inspection | `uv run python .cursor/supabase_tool.py` |
| `list_all_supabase_tables.py` | Discover all tables | `uv run python .cursor/list_all_supabase_tables.py` |
| `get_actual_columns.py` | Find actual column structure | `uv run python .cursor/get_actual_columns.py` |

---

## 🚀 Getting Started

### 1. View Current Data
```bash
# Inspect all tables
uv run python .cursor/list_all_supabase_tables.py

# View specific user data
uv run python .cursor/supabase_tool.py 03f6b167-0c4d-4983-a380-54b8eb42f830
```

### 2. Add Test Data
```sql
-- In Supabase SQL Editor
-- Copy/paste: database/create_demo_data.sql
```

### 3. Query Examples
```sql
-- Get user's watchlist
SELECT watchlist_stocks FROM users WHERE id = 'user-uuid';

-- Find active conversations
SELECT * FROM conversation_sessions WHERE is_active = true;

-- Get recent messages in a session
SELECT role, content, created_at 
FROM conversation_messages 
WHERE session_id = 'session-uuid' 
ORDER BY created_at;

-- Latest news articles
SELECT title, summary, published_at 
FROM news_articles 
ORDER BY published_at DESC 
LIMIT 10;
```

---

## ⚠️ Schema Status & Limitations

### What's Working ✅
- User accounts with preferences and watchlists
- Conversation session tracking
- Message history with metadata
- Basic news article caching
- WebSocket integration

### What's Missing ❌
Compared to the full `schema.sql` plan:

**Missing Tables (5)**:
- `user_preferences` - Extended user settings
- `news_sources` - News provider configuration  
- `stock_data` - Stock price caching
- `user_interactions` - Usage analytics
- `ai_response_cache` - AI response caching

**Missing Columns**:
- `conversation_messages`: No `audio_url`, `processing_time_ms`, `confidence_score`
- `news_articles`: No `sentiment_score`, `topics`, `keywords`, `is_breaking`

### Workarounds 💡
- Store missing data in `metadata` JSONB columns
- Use external APIs for missing features
- Add columns incrementally as features are built

---

## 🔐 Security & Access

### Authentication
- Uses Supabase Auth for user management
- JWT tokens for API access
- Row Level Security (RLS) for data isolation

### Current RLS Policies
```sql
-- Users can only see their own data
CREATE POLICY "Users can view own data" ON users 
FOR ALL USING (auth.uid() = id);

-- Public read access to news
CREATE POLICY "Public read access" ON news_articles 
FOR SELECT USING (true);
```

### API Access
```bash
# Test watchlist endpoint
curl "http://localhost:8000/api/user/watchlist?user_id=03f6b167-0c4d-4983-a380-54b8eb42f830"
# Returns: {"watchlist_stocks":["TSLA"]}
```

---

## 📊 Performance Considerations

### Query Optimization
- Index on `published_at` for latest news queries
- Index on `session_id` for conversation history
- GIN index on `title` for full-text search

### Caching Strategy
- News articles cached to reduce API calls
- User preferences cached in application layer
- AI responses could be cached (table exists in schema.sql)

### Scaling Notes
- Current schema supports ~10K users
- Message table will grow quickly with voice interactions
- Consider partitioning by date for large deployments

---

## 🛠️ Development Workflow

### Making Schema Changes
1. **Test locally** with Python tools
2. **Update documentation** in this README
3. **Run migrations** in Supabase SQL Editor
4. **Update application code** to use new fields
5. **Test thoroughly** with voice interactions

### Adding New Tables
1. Define in `schema.sql`
2. Create in Supabase dashboard or SQL Editor
3. Add RLS policies if needed
4. Update this README
5. Create Python inspection tools

### Debugging Database Issues
```bash
# Check what tables exist
uv run python .cursor/list_all_supabase_tables.py

# Inspect specific table structure  
uv run python .cursor/get_actual_columns.py

# Test RLS policies
uv run python .cursor/check_rls_policies.py

# View user data
uv run python .cursor/supabase_tool.py [user_id]
```

---

## 📞 Support & Resources

### Supabase Dashboard
- **URL**: https://app.supabase.com/project/zaipmdlbcraufolrizpn
- **SQL Editor**: https://app.supabase.com/project/zaipmdlbcraufolrizpn/sql
- **Table Editor**: https://app.supabase.com/project/zaipmdlbcraufolrizpn/editor

### Documentation
- **Supabase Docs**: https://supabase.com/docs
- **PostgreSQL Docs**: https://postgresql.org/docs/
- **This README**: Complete database reference

### Common Issues
1. **Empty results**: Check RLS policies and user permissions
2. **Column not found**: Verify actual schema vs expected
3. **Connection errors**: Check environment variables
4. **Slow queries**: Review indexes and query patterns

---

## 🎯 Future Roadmap

### Phase 1: Core Stability
- ✅ Basic schema working
- ✅ User preferences and watchlists
- ✅ Conversation tracking
- ⏳ RLS policy fixes

### Phase 2: Enhanced Features
- 📋 Add missing columns to existing tables
- 📋 Implement news source management
- 📋 Add stock price caching
- 📋 User interaction analytics

### Phase 3: Advanced Features
- 📋 AI response caching
- 📋 Sentiment analysis
- 📋 Advanced personalization
- 📋 Performance optimization

### Phase 4: Production Ready
- 📋 Full schema implementation
- 📋 Automated migrations
- 📋 Monitoring and alerting
- 📋 Backup and recovery

---

**Database Version**: 0.1 (Minimal Schema)  
**Completion**: 35% of planned features  
**Status**: ✅ Working for basic voice interactions  
**Next Priority**: Fix RLS policies for anon key access

---

*Last updated: 2025-10-12 by database inspection tools*




