"""Wrapper for existing NewsAgent to integrate with FastAPI backend."""
import asyncio
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# Add the parent directory to Python path to import existing agent
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from src.agent import NewsAgent
    from src.memory import conversation_memory
    import src.config as config
except ImportError as e:
    print(f"Warning: Could not import existing agent modules: {e}")
    NewsAgent = None
    conversation_memory = None
    config = None

from ..database import get_database
from ..cache import get_cache


class AgentWrapper:
    """Wrapper for existing NewsAgent with database and cache integration."""
    
    def __init__(self):
        self.agent = None
        self.memory = None
        self.db = None
        self.cache = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the agent wrapper."""
        if self._initialized:
            return
        
        try:
            # Initialize database and cache
            self.db = await get_database()
            self.cache = await get_cache()
            
            # Initialize existing agent if available
            if NewsAgent:
                self.agent = NewsAgent()
                self.memory = conversation_memory
                print("✅ Existing NewsAgent initialized successfully")
            else:
                print("⚠️ Existing NewsAgent not available, using mock implementation")
                self.agent = MockNewsAgent()
                self.memory = MockMemory()
            
            self._initialized = True
            print("✅ AgentWrapper initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize AgentWrapper: {e}")
            raise
    
    async def process_text_command(self, command: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Process text command through the agent."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Check cache first
            cache_key = f"ai:response:{hash(command)}"
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                print(f"📦 Using cached response for command: {command[:50]}...")
                return {
                    "response_text": cached_response,
                    "response_type": "cached",
                    "processing_time_ms": 0,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Process through agent
            start_time = datetime.now()
            
            if self.agent:
                # Run synchronous agent method in thread pool to avoid blocking
                if asyncio.iscoroutinefunction(self.agent.get_response):
                    response_text = await self.agent.get_response(command)
                else:
                    # Wrap synchronous call in asyncio.to_thread
                    response_text = await asyncio.to_thread(self.agent.get_response, command)
            else:
                response_text = f"Mock response for: {command}"
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Cache the response
            await self.cache.set(cache_key, response_text, ttl=3600)
            
            # Store conversation in database
            await self._store_conversation(user_id, session_id, command, response_text, processing_time)
            
            # Track user interaction
            await self.db.track_user_interaction(
                user_id=user_id,
                interaction_type="text_command",
                target_content=command,
                success=True,
                response_time_ms=int(processing_time)
            )
            
            return {
                "response_text": response_text,
                "response_type": "agent_response",
                "processing_time_ms": int(processing_time),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error processing text command: {e}")
            return {
                "response_text": f"Sorry, I encountered an error processing your request: {str(e)}",
                "response_type": "error",
                "processing_time_ms": 0,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_voice_command(self, command: str, user_id: str, session_id: str,
                                  audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Process voice command through the agent."""
        try:
            if not self._initialized:
                await self.initialize()

            # Process the command (same as text for now)
            result = await self.process_text_command(command, user_id, session_id)

            # Add voice-specific metadata
            result["audio_url"] = audio_url
            result["command_type"] = "voice"

            return result

        except Exception as e:
            print(f"❌ Error processing voice command: {e}")
            return {
                "response_text": f"Sorry, I encountered an error processing your voice command: {str(e)}",
                "response_type": "error",
                "processing_time_ms": 0,
                "session_id": session_id,
                "audio_url": audio_url,
                "command_type": "voice",
                "timestamp": datetime.now().isoformat()
            }

    async def stream_voice_response(self, command: str, user_id: str, session_id: str):
        """
        Stream agent response in real-time for voice commands.
        This enables concurrent TTS generation while the LLM is still generating.

        Yields:
            str: Text chunks as they are generated
        """
        try:
            if not self._initialized:
                await self.initialize()

            start_time = datetime.now()

            if self.agent and hasattr(self.agent, 'get_response_stream'):
                # Stream response from agent
                async for text_chunk in self.agent.get_response_stream(command):
                    yield text_chunk
            else:
                # Fallback to non-streaming if agent doesn't support streaming
                print("⚠️ Agent does not support streaming, falling back to non-streaming")
                if asyncio.iscoroutinefunction(self.agent.get_response):
                    response_text = await self.agent.get_response(command)
                else:
                    response_text = await asyncio.to_thread(self.agent.get_response, command)
                yield response_text

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Track user interaction
            await self.db.track_user_interaction(
                user_id=user_id,
                interaction_type="voice_command_stream",
                target_content=command,
                success=True,
                response_time_ms=int(processing_time)
            )

        except Exception as e:
            print(f"❌ Error streaming voice response: {e}")
            yield f"Sorry, I encountered an error processing your request: {str(e)}"
    
    async def get_news_latest(self, topics: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest news articles."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Check cache first
            cache_key = f"news:latest:{':'.join(sorted(topics or []))}:{limit}"
            cached_news = await self.cache.get(cache_key)
            if cached_news:
                print(f"📦 Using cached news for topics: {topics}")
                return cached_news
            
            # Get from database
            news_items = await self.db.get_latest_news(topics or [], limit)
            
            # Cache the results
            await self.cache.set(cache_key, news_items, ttl=900)  # 15 minutes
            
            return news_items
            
        except Exception as e:
            print(f"❌ Error getting latest news: {e}")
            return []
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data for a symbol."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Check cache first
            cache_key = f"stock:price:{symbol.upper()}"
            cached_stock = await self.cache.get(cache_key)
            if cached_stock:
                print(f"📦 Using cached stock data for: {symbol}")
                return cached_stock
            
            # Get from database
            stock_data = await self.db.get_stock_data(symbol)
            
            # Cache the results
            if stock_data:
                await self.cache.set(cache_key, stock_data, ttl=60)  # 1 minute
            
            return stock_data
            
        except Exception as e:
            print(f"❌ Error getting stock data for {symbol}: {e}")
            return None
    
    async def search_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search news articles."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Check cache first
            cache_key = f"news:search:{hash(query)}:{limit}"
            cached_results = await self.cache.get(cache_key)
            if cached_results:
                print(f"📦 Using cached search results for: {query}")
                return cached_results
            
            # Search in database
            news_items = await self.db.search_news(query, limit)
            
            # Cache the results
            await self.cache.set(cache_key, news_items, ttl=1800)  # 30 minutes
            
            return news_items
            
        except Exception as e:
            print(f"❌ Error searching news: {e}")
            return []
    
    async def _store_conversation(self, user_id: str, session_id: str, 
                                user_input: str, agent_response: str, 
                                processing_time_ms: int):
        """Store conversation in database."""
        try:
            # Store user input
            await self.db.add_conversation_message(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=user_input,
                metadata={"processing_time_ms": processing_time_ms}
            )
            
            # Store agent response
            await self.db.add_conversation_message(
                session_id=session_id,
                user_id=user_id,
                role="agent",
                content=agent_response,
                metadata={"processing_time_ms": processing_time_ms}
            )
        except Exception as e:
            print(f"❌ Error storing conversation: {e}")

    async def update_watchlist(self, user_id: str, symbols: List[str]) -> Dict[str, Any]:
        """Update user's watchlist stocks directly via database accessor."""
        if not self._initialized:
            await self.initialize()
        prefs = await self.db.get_user_preferences(user_id) or {}
        current = set(prefs.get("watchlist_stocks", []))
        updated = sorted(current.union({s.upper() for s in symbols if s}))
        ok = await self.db.update_user_preferences(user_id, {"watchlist_stocks": updated})
        if ok:
            await self.cache.delete(f"user:preferences:{user_id}")
        return {"updated": ok, "watchlist": updated}
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Check cache first
            cache_key = f"user:preferences:{user_id}"
            cached_prefs = await self.cache.get(cache_key)
            if cached_prefs:
                return cached_prefs
            
            # Get from database
            prefs = await self.db.get_user_preferences(user_id)
            
            # Cache the results
            if prefs:
                await self.cache.set(cache_key, prefs, ttl=3600)  # 1 hour
            
            return prefs or {}
            
        except Exception as e:
            print(f"❌ Error getting user preferences: {e}")
            return {}
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Update in database
            success = await self.db.update_user_preferences(user_id, preferences)
            
            if success:
                # Invalidate cache
                cache_key = f"user:preferences:{user_id}"
                await self.cache.delete(cache_key)
            
            return success
            
        except Exception as e:
            print(f"❌ Error updating user preferences: {e}")
            return False


class MockNewsAgent:
    """Mock NewsAgent for testing when original is not available."""
    
    async def get_response(self, command: str) -> str:
        """Mock response generation."""
        command_lower = command.lower()
        
        if "news" in command_lower:
            return "Here are the latest headlines: 1. Technology sector shows strong growth. 2. Market indices reach new highs. 3. Renewable energy investments surge."
        elif "stock" in command_lower or "price" in command_lower:
            return "Current market data: S&P 500 is up 0.5%, NASDAQ is up 0.8%, and Dow Jones is up 0.3%."
        elif "tell me more" in command_lower:
            return "I'd be happy to provide more details. Could you please specify which topic you'd like me to elaborate on?"
        elif "help" in command_lower:
            return "I can help you with: 1. Latest news updates 2. Stock prices and market data 3. Detailed explanations of topics 4. Voice commands and interactions"
        else:
            return f"I understand you said: '{command}'. How can I assist you further?"


class MockMemory:
    """Mock memory for testing when original is not available."""
    
    def __init__(self):
        self.context_history = []
    
    def add_context(self, user_input: str, agent_response: str, 
                   news_items: List[Dict[str, Any]] = None, topic: str = "general"):
        """Mock context addition."""
        self.context_history.append({
            "user_input": user_input,
            "agent_response": agent_response,
            "news_items": news_items or [],
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_deep_dive_context(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Mock deep dive context."""
        return None


# Global agent wrapper instance
agent_wrapper = AgentWrapper()


async def get_agent() -> AgentWrapper:
    """Get agent wrapper instance."""
    if not agent_wrapper._initialized:
        await agent_wrapper.initialize()
    return agent_wrapper
