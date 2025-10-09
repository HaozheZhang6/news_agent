# Upstash Redis Cache Strategy for Voice News Agent

## Cache Architecture Overview

### Cache Layers
1. **News Cache** - Cached news articles and summaries
2. **AI Response Cache** - Cached LLM responses for performance
3. **User Session Cache** - Active user sessions and preferences
4. **Voice Cache** - Audio files and transcriptions
5. **Stock Data Cache** - Real-time stock prices and market data

## Cache Keys Structure

### News Cache Keys
```
news:latest:{topics}:{limit}           # Latest news by topics
news:article:{article_id}              # Individual article
news:summary:{article_id}:{type}       # Brief/deep-dive summaries
news:search:{query_hash}               # Search results
news:breaking:{timestamp}              # Breaking news alerts
```

### AI Response Cache Keys
```
ai:response:{prompt_hash}               # LLM responses
ai:summary:{content_hash}               # News summaries
ai:translation:{text_hash}:{lang}      # Translations
ai:sentiment:{text_hash}                # Sentiment analysis
```

### User Session Cache Keys
```
user:session:{user_id}                 # Active user session
user:preferences:{user_id}             # User preferences
user:watchlist:{user_id}               # Stock watchlist
user:topics:{user_id}                  # Preferred topics
user:conversation:{session_id}         # Conversation context
```

### Voice Cache Keys
```
voice:audio:{session_id}:{timestamp}   # Audio files
voice:transcription:{audio_hash}        # Speech-to-text results
voice:tts:{text_hash}:{voice}          # Text-to-speech audio
voice:interruption:{session_id}        # Interruption state
```

### Stock Data Cache Keys
```
stock:price:{symbol}                   # Current stock price
stock:watchlist:{user_id}              # User's watchlist prices
stock:news:{symbol}                    # Stock-related news
stock:analysis:{symbol}:{period}       # Technical analysis
```

## Cache TTL (Time To Live) Strategy

### Short-term Cache (1-5 minutes)
- Stock prices: 1 minute
- Breaking news: 2 minutes
- Voice transcriptions: 5 minutes
- User session data: 5 minutes

### Medium-term Cache (15-60 minutes)
- News articles: 15 minutes
- AI summaries: 30 minutes
- Search results: 30 minutes
- User preferences: 60 minutes

### Long-term Cache (1-24 hours)
- AI responses: 1 hour
- Stock analysis: 4 hours
- News summaries: 6 hours
- User watchlists: 24 hours

## Implementation Examples

### Python Cache Service
```python
import redis
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(
            os.getenv("UPSTASH_REDIS_REST_URL"),
            password=os.getenv("UPSTASH_REDIS_REST_TOKEN")
        )
    
    async def get_news_latest(self, topics: list, limit: int = 10) -> Optional[list]:
        """Get cached latest news"""
        key = f"news:latest:{':'.join(topics)}:{limit}"
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None
    
    async def set_news_latest(self, topics: list, news: list, ttl: int = 900):
        """Cache latest news for 15 minutes"""
        key = f"news:latest:{':'.join(topics)}:{len(news)}"
        await self.redis.setex(key, ttl, json.dumps(news))
    
    async def get_ai_response(self, prompt: str) -> Optional[str]:
        """Get cached AI response"""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        key = f"ai:response:{prompt_hash}"
        return await self.redis.get(key)
    
    async def set_ai_response(self, prompt: str, response: str, ttl: int = 3600):
        """Cache AI response for 1 hour"""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        key = f"ai:response:{prompt_hash}"
        await self.redis.setex(key, ttl, response)
    
    async def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Get active user session"""
        key = f"user:session:{user_id}"
        cached = await self.redis.get(key)
        return json.loads(cached) if cached else None
    
    async def set_user_session(self, user_id: str, session_data: Dict, ttl: int = 300):
        """Cache user session for 5 minutes"""
        key = f"user:session:{user_id}"
        await self.redis.setex(key, ttl, json.dumps(session_data))
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all user-related cache"""
        pattern = f"user:*:{user_id}"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

## Cache Warming Strategy

### Preload Critical Data
```python
async def warm_cache():
    """Preload frequently accessed data"""
    
    # Preload latest news for common topics
    common_topics = ['technology', 'finance', 'politics', 'general']
    for topic in common_topics:
        news = await fetch_latest_news([topic])
        await cache_service.set_news_latest([topic], news)
    
    # Preload popular stock data
    popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
    for symbol in popular_stocks:
        price = await fetch_stock_price(symbol)
        await cache_service.set_stock_price(symbol, price)
    
    # Preload AI responses for common queries
    common_queries = [
        "tell me the news",
        "what's the stock market doing",
        "latest technology news"
    ]
    for query in common_queries:
        response = await ai_service.generate_response(query)
        await cache_service.set_ai_response(query, response)
```

## Cache Invalidation Strategy

### Event-Based Invalidation
```python
async def invalidate_on_news_update():
    """Invalidate cache when new news arrives"""
    # Clear latest news cache
    await redis.delete("news:latest:*")
    
    # Clear breaking news cache
    await redis.delete("news:breaking:*")
    
    # Clear topic-specific cache
    await redis.delete("news:topic:*")

async def invalidate_on_stock_update(symbol: str):
    """Invalidate cache when stock data updates"""
    # Clear stock price cache
    await redis.delete(f"stock:price:{symbol}")
    
    # Clear watchlist cache for users tracking this stock
    await redis.delete(f"stock:watchlist:*")

async def invalidate_on_user_preference_change(user_id: str):
    """Invalidate cache when user preferences change"""
    # Clear user-specific cache
    await redis.delete(f"user:*:{user_id}")
    
    # Clear personalized news cache
    await redis.delete(f"news:personalized:{user_id}")
```

## Performance Optimization

### Batch Operations
```python
async def batch_get_news(article_ids: list) -> Dict[str, Any]:
    """Batch get multiple news articles"""
    keys = [f"news:article:{id}" for id in article_ids]
    cached_items = await redis.mget(keys)
    
    result = {}
    for i, cached in enumerate(cached_items):
        if cached:
            result[article_ids[i]] = json.loads(cached)
    
    return result

async def batch_set_news(news_items: Dict[str, Any]):
    """Batch set multiple news articles"""
    pipe = redis.pipeline()
    for article_id, data in news_items.items():
        key = f"news:article:{article_id}"
        pipe.setex(key, 900, json.dumps(data))  # 15 minutes TTL
    await pipe.execute()
```

### Compression for Large Data
```python
import gzip
import base64

async def set_compressed_data(key: str, data: Any, ttl: int):
    """Store compressed data in cache"""
    json_data = json.dumps(data)
    compressed = gzip.compress(json_data.encode())
    encoded = base64.b64encode(compressed).decode()
    await redis.setex(key, ttl, encoded)

async def get_compressed_data(key: str) -> Optional[Any]:
    """Retrieve and decompress data from cache"""
    encoded = await redis.get(key)
    if not encoded:
        return None
    
    compressed = base64.b64decode(encoded)
    json_data = gzip.decompress(compressed).decode()
    return json.loads(json_data)
```

## Monitoring and Analytics

### Cache Hit Rate Monitoring
```python
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

# Usage in cache service
async def get_with_metrics(self, key: str) -> Optional[Any]:
    result = await self.redis.get(key)
    if result:
        self.metrics.record_hit()
    else:
        self.metrics.record_miss()
    return result
```

## Upstash-Specific Features

### REST API Usage
```python
# Upstash Redis REST API client
import httpx

class UpstashRedisClient:
    def __init__(self):
        self.url = os.getenv("UPSTASH_REDIS_REST_URL")
        self.token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        self.client = httpx.AsyncClient()
    
    async def get(self, key: str) -> Optional[str]:
        response = await self.client.get(
            f"{self.url}/get/{key}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json().get("result")
    
    async def setex(self, key: str, ttl: int, value: str):
        await self.client.post(
            f"{self.url}/setex/{key}/{ttl}",
            headers={"Authorization": f"Bearer {self.token}"},
            content=value
        )
```

This cache strategy will significantly improve your voice news agent's performance by reducing API calls, database queries, and AI processing time while maintaining data freshness.
