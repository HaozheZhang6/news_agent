"""Database connection and management for Supabase."""
from typing import Optional, Dict, Any, List
from supabase import create_client
from .config import get_settings

settings = get_settings()

class DatabaseManager:
    """Supabase database manager."""
    
    def __init__(self):
        self.client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Supabase client."""
        if self._initialized:
            return
            
        try:
            # Simple client creation without proxy or extra options
            self.client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self._initialized = True
            print("✅ Supabase client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            if not self.client:
                await self.initialize()
            
            # Simple query to test connection
            result = self.client.table('users').select('id').limit(1).execute()
            return True
        except Exception as e:
            print(f"❌ Database health check failed: {e}")
            return False
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            result = self.client.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Error getting user {user_id}: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user."""
        try:
            result = self.client.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences stored directly on users table.

        Only columns that exist on users are updated (preferred_topics, watchlist_stocks).
        """
        try:
            update_payload: Dict[str, Any] = {}
            if 'preferred_topics' in preferences:
                update_payload['preferred_topics'] = preferences['preferred_topics']
            if 'watchlist_stocks' in preferences:
                update_payload['watchlist_stocks'] = preferences['watchlist_stocks']
            if not update_payload:
                return True
            result = (
                self.client
                .table('users')
                .update(update_payload)
                .eq('id', user_id)
                .execute()
            )
            return result.data is not None
        except Exception as e:
            print(f"❌ Error updating user preferences: {e}")
            return False
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences stored on users table."""
        try:
            result = (
                self.client
                .table('users')
                .select('preferred_topics, watchlist_stocks')
                .eq('id', user_id)
                .execute()
            )
            if result.data:
                row = result.data[0]
                return {
                    'preferred_topics': row.get('preferred_topics') or [],
                    'watchlist_stocks': row.get('watchlist_stocks') or [],
                }
            return None
        except Exception as e:
            print(f"❌ Error getting user preferences: {e}")
            return None
    
    async def create_conversation_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Create new conversation session."""
        try:
            session_data = {
                'user_id': user_id,
                'session_start': 'now()',
                'is_active': True
            }
            result = self.client.table('conversation_sessions').insert(session_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Error creating conversation session: {e}")
            return None
    
    async def add_conversation_message(self, session_id: str, user_id: str,
                                       role: str, content: str,
                                       metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Add message to conversation using 'role' column (user|agent|system)."""
        try:
            message_data = {
                'session_id': session_id,
                'user_id': user_id,
                'role': role,
                'content': content,
                'metadata': metadata or {}
            }
            result = self.client.table('conversation_messages').insert(message_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Error adding conversation message: {e}")
            return None
    
    async def get_conversation_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation messages for a session."""
        try:
            result = self.client.table('conversation_messages').select('*').eq('session_id', session_id).order('created_at', desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            print(f"❌ Error getting conversation messages: {e}")
            return []
    
    async def get_latest_news(self, topics: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest news articles."""
        try:
            query = self.client.table('news_articles').select('*, news_sources(*)').order('published_at', desc=True).limit(limit)
            
            if topics:
                query = query.overlaps('topics', topics)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            print(f"❌ Error getting latest news: {e}")
            return []
    
    async def search_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search news articles."""
        try:
            result = self.client.table('news_articles').select('*, news_sources(*)').text_search('title,summary', query).limit(limit).execute()
            return result.data or []
        except Exception as e:
            print(f"❌ Error searching news: {e}")
            return []
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data for symbol."""
        try:
            result = self.client.table('stock_data').select('*').eq('symbol', symbol.upper()).order('last_updated', desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Error getting stock data for {symbol}: {e}")
            return None
    
    async def track_user_interaction(self, user_id: str, interaction_type: str, 
                                   target_content: str = None, success: bool = True,
                                   response_time_ms: int = None) -> bool:
        """Track user interaction for analytics."""
        try:
            interaction_data = {
                'user_id': user_id,
                'interaction_type': interaction_type,
                'target_content': target_content,
                'success': success,
                'response_time_ms': response_time_ms
            }
            result = self.client.table('user_interactions').insert(interaction_data).execute()
            return bool(result.data)
        except Exception as e:
            print(f"❌ Error tracking user interaction: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> DatabaseManager:
    """Get database manager instance."""
    if not db_manager._initialized:
        await db_manager.initialize()
    return db_manager
