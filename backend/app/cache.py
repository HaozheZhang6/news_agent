"""Cache management for Upstash Redis."""
import json
import hashlib
import asyncio
from typing import Optional, Any, Dict, List
import httpx
from .config import get_settings

settings = get_settings()

class CacheManager:
    """Upstash Redis cache manager."""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = settings.upstash_redis_rest_url
        self.token = settings.upstash_redis_rest_token
        self._initialized = False
    
    async def initialize(self):
        """Initialize Upstash Redis client."""
        if self._initialized:
            return
            
        try:
            self.client = httpx.AsyncClient(
                timeout=10.0,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
            )
            self._initialized = True
            print("✅ Upstash Redis client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Upstash Redis client: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check cache connection health."""
        try:
            if not self.client:
                await self.initialize()
            
            response = await self.client.get(f"{self.base_url}/ping")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Cache health check failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if not self.client:
                await self.initialize()
            
            response = await self.client.get(f"{self.base_url}/get/{key}")
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    return json.loads(result["result"])
            return None
        except Exception as e:
            print(f"❌ Error getting cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache."""
        try:
            if not self.client:
                await self.initialize()
            
            json_value = json.dumps(value)
            url = f"{self.base_url}/set/{key}"
            
            if ttl:
                url += f"/ex/{ttl}"
            
            response = await self.client.post(url, content=json_value)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if not self.client:
                await self.initialize()
            
            response = await self.client.post(f"{self.base_url}/del/{key}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if not self.client:
                await self.initialize()
            
            response = await self.client.get(f"{self.base_url}/exists/{key}")
            if response.status_code == 200:
                result = response.json()
                return result.get("result", 0) > 0
            return False
        except Exception as e:
            print(f"❌ Error checking cache key {key}: {e}")
            return False
    
    async def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        try:
            if not self.client:
                await self.initialize()
            
            response = await self.client.post(f"{self.base_url}/mget", json=keys)
            if response.status_code == 200:
                result = response.json()
                values = result.get("result", [])
                return {key: json.loads(val) if val else None for key, val in zip(keys, values)}
            return {}
        except Exception as e:
            print(f"❌ Error getting multiple cache keys: {e}")
            return {}
    
    async def set_multiple(self, data: Dict[str, Any], ttl: int = None) -> bool:
        """Set multiple values in cache."""
        try:
            if not self.client:
                await self.initialize()
            
            # Convert values to JSON strings
            json_data = {key: json.dumps(value) for key, value in data.items()}
            
            response = await self.client.post(f"{self.base_url}/mset", json=json_data)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error setting multiple cache keys: {e}")
            return False
    
    # News-specific cache methods
    async def get_news_latest(self, topics: List[str], limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get cached latest news."""
        key = f"news:latest:{':'.join(sorted(topics))}:{limit}"
        return await self.get(key)
    
    async def set_news_latest(self, topics: List[str], news: List[Dict[str, Any]], ttl: int = 900):
        """Cache latest news for 15 minutes."""
        key = f"news:latest:{':'.join(sorted(topics))}:{len(news)}"
        await self.set(key, news, ttl)
    
    async def get_news_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get cached news article."""
        key = f"news:article:{article_id}"
        return await self.get(key)
    
    async def set_news_article(self, article_id: str, article: Dict[str, Any], ttl: int = 900):
        """Cache news article for 15 minutes."""
        key = f"news:article:{article_id}"
        await self.set(key, article, ttl)
    
    # AI response cache methods
    async def get_ai_response(self, prompt: str) -> Optional[str]:
        """Get cached AI response."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        key = f"ai:response:{prompt_hash}"
        return await self.get(key)
    
    async def set_ai_response(self, prompt: str, response: str, ttl: int = 3600):
        """Cache AI response for 1 hour."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        key = f"ai:response:{prompt_hash}"
        await self.set(key, response, ttl)
    
    # User session cache methods
    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get active user session."""
        key = f"user:session:{user_id}"
        return await self.get(key)
    
    async def set_user_session(self, user_id: str, session_data: Dict[str, Any], ttl: int = 300):
        """Cache user session for 5 minutes."""
        key = f"user:session:{user_id}"
        await self.set(key, session_data, ttl)
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user preferences."""
        key = f"user:preferences:{user_id}"
        return await self.get(key)
    
    async def set_user_preferences(self, user_id: str, preferences: Dict[str, Any], ttl: int = 3600):
        """Cache user preferences for 1 hour."""
        key = f"user:preferences:{user_id}"
        await self.set(key, preferences, ttl)
    
    # Stock data cache methods
    async def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached stock price."""
        key = f"stock:price:{symbol.upper()}"
        return await self.get(key)
    
    async def set_stock_price(self, symbol: str, price_data: Dict[str, Any], ttl: int = 60):
        """Cache stock price for 1 minute."""
        key = f"stock:price:{symbol.upper()}"
        await self.set(key, price_data, ttl)
    
    async def get_user_watchlist(self, user_id: str) -> Optional[List[str]]:
        """Get cached user watchlist."""
        key = f"user:watchlist:{user_id}"
        return await self.get(key)
    
    async def set_user_watchlist(self, user_id: str, watchlist: List[str], ttl: int = 3600):
        """Cache user watchlist for 1 hour."""
        key = f"user:watchlist:{user_id}"
        await self.set(key, watchlist, ttl)
    
    # Voice cache methods
    async def get_voice_transcription(self, audio_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached voice transcription."""
        key = f"voice:transcription:{audio_hash}"
        return await self.get(key)
    
    async def set_voice_transcription(self, audio_hash: str, transcription: Dict[str, Any], ttl: int = 300):
        """Cache voice transcription for 5 minutes."""
        key = f"voice:transcription:{audio_hash}"
        await self.set(key, transcription, ttl)
    
    async def get_tts_audio(self, text_hash: str, voice: str) -> Optional[str]:
        """Get cached TTS audio URL."""
        key = f"voice:tts:{text_hash}:{voice}"
        return await self.get(key)
    
    async def set_tts_audio(self, text_hash: str, voice: str, audio_url: str, ttl: int = 3600):
        """Cache TTS audio URL for 1 hour."""
        key = f"voice:tts:{text_hash}:{voice}"
        await self.set(key, audio_url, ttl)
    
    # Cache management methods
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all user-related cache."""
        patterns = [
            f"user:session:{user_id}",
            f"user:preferences:{user_id}",
            f"user:watchlist:{user_id}",
            f"user:conversation:{user_id}"
        ]
        
        for pattern in patterns:
            await self.delete(pattern)
    
    async def invalidate_news_cache(self):
        """Invalidate news-related cache."""
        # Note: Upstash Redis doesn't support pattern deletion via REST API
        # This would need to be implemented with a different approach
        pass
    
    async def cleanup_expired_cache(self):
        """Clean up expired cache entries."""
        # Upstash Redis automatically handles TTL expiration
        # This method is here for future enhancements
        pass


# Global cache manager instance
cache_manager = CacheManager()


async def get_cache() -> CacheManager:
    """Get cache manager instance."""
    if not cache_manager._initialized:
        await cache_manager.initialize()
    return cache_manager
