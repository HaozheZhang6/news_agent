"""Tests for agent wrapper core component."""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from backend.app.core.agent_wrapper import AgentWrapper, MockNewsAgent, MockMemory


class TestAgentWrapper:
    """Test agent wrapper functionality."""
    
    @pytest.fixture
    async def agent_wrapper(self, mock_database, mock_cache):
        """Create agent wrapper instance for testing."""
        wrapper = AgentWrapper()
        wrapper.db = mock_database
        wrapper.cache = mock_cache
        wrapper._initialized = True
        return wrapper
    
    async def test_initialize_with_existing_agent(self, mock_database, mock_cache):
        """Test initialization with existing NewsAgent."""
        with patch('backend.app.core.agent_wrapper.NewsAgent') as mock_news_agent:
            with patch('backend.app.core.agent_wrapper.conversation_memory') as mock_memory:
                mock_agent_instance = Mock()
                mock_news_agent.return_value = mock_agent_instance
                
                wrapper = AgentWrapper()
                wrapper.db = mock_database
                wrapper.cache = mock_cache
                
                await wrapper.initialize()
                
                assert wrapper.agent == mock_agent_instance
                assert wrapper.memory == mock_memory
                assert wrapper._initialized is True
    
    async def test_initialize_without_existing_agent(self, mock_database, mock_cache):
        """Test initialization without existing NewsAgent."""
        with patch('backend.app.core.agent_wrapper.NewsAgent', None):
            with patch('backend.app.core.agent_wrapper.conversation_memory', None):
                wrapper = AgentWrapper()
                wrapper.db = mock_database
                wrapper.cache = mock_cache
                
                await wrapper.initialize()
                
                assert isinstance(wrapper.agent, MockNewsAgent)
                assert isinstance(wrapper.memory, MockMemory)
                assert wrapper._initialized is True
    
    async def test_process_text_command(self, agent_wrapper):
        """Test processing text command."""
        with patch.object(agent_wrapper, 'agent') as mock_agent:
            mock_agent.get_response = AsyncMock(return_value="Test response")
            
            result = await agent_wrapper.process_text_command(
                command="tell me the news",
                user_id="test-user",
                session_id="test-session"
            )
            
            assert result["response_text"] == "Test response"
            assert result["response_type"] == "agent_response"
            assert result["session_id"] == "test-session"
            assert "processing_time_ms" in result
            assert "timestamp" in result
    
    async def test_process_text_command_with_cache(self, agent_wrapper):
        """Test processing text command with cached response."""
        agent_wrapper.cache.get.return_value = "Cached response"
        
        result = await agent_wrapper.process_text_command(
            command="tell me the news",
            user_id="test-user",
            session_id="test-session"
        )
        
        assert result["response_text"] == "Cached response"
        assert result["response_type"] == "cached"
        assert result["processing_time_ms"] == 0
    
    async def test_process_voice_command(self, agent_wrapper):
        """Test processing voice command."""
        with patch.object(agent_wrapper, 'process_text_command') as mock_process:
            mock_process.return_value = {
                "response_text": "Voice response",
                "response_type": "agent_response",
                "processing_time_ms": 150,
                "session_id": "test-session",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            result = await agent_wrapper.process_voice_command(
                command="tell me the news",
                user_id="test-user",
                session_id="test-session",
                audio_url="https://example.com/audio.mp3"
            )
            
            assert result["response_text"] == "Voice response"
            assert result["audio_url"] == "https://example.com/audio.mp3"
            assert result["command_type"] == "voice"
            mock_process.assert_called_once()
    
    async def test_get_news_latest(self, agent_wrapper):
        """Test getting latest news."""
        agent_wrapper.db.get_latest_news.return_value = [
            {"id": "news-1", "title": "Test News", "topics": ["technology"]}
        ]
        
        result = await agent_wrapper.get_news_latest(["technology"], 10)
        
        assert len(result) == 1
        assert result[0]["title"] == "Test News"
        agent_wrapper.db.get_latest_news.assert_called_once_with(["technology"], 10)
    
    async def test_get_news_latest_with_cache(self, agent_wrapper):
        """Test getting latest news with cached data."""
        cached_news = [{"id": "news-1", "title": "Cached News"}]
        agent_wrapper.cache.get.return_value = cached_news
        
        result = await agent_wrapper.get_news_latest(["technology"], 10)
        
        assert result == cached_news
        agent_wrapper.db.get_latest_news.assert_not_called()
    
    async def test_get_stock_data(self, agent_wrapper):
        """Test getting stock data."""
        agent_wrapper.db.get_stock_data.return_value = {
            "symbol": "AAPL",
            "current_price": 150.0
        }
        
        result = await agent_wrapper.get_stock_data("AAPL")
        
        assert result["symbol"] == "AAPL"
        assert result["current_price"] == 150.0
        agent_wrapper.db.get_stock_data.assert_called_once_with("AAPL")
    
    async def test_get_stock_data_with_cache(self, agent_wrapper):
        """Test getting stock data with cached data."""
        cached_stock = {"symbol": "AAPL", "current_price": 150.0}
        agent_wrapper.cache.get.return_value = cached_stock
        
        result = await agent_wrapper.get_stock_data("AAPL")
        
        assert result == cached_stock
        agent_wrapper.db.get_stock_data.assert_not_called()
    
    async def test_search_news(self, agent_wrapper):
        """Test searching news."""
        agent_wrapper.db.search_news.return_value = [
            {"id": "news-1", "title": "Search Result"}
        ]
        
        result = await agent_wrapper.search_news("apple", 10)
        
        assert len(result) == 1
        assert result[0]["title"] == "Search Result"
        agent_wrapper.db.search_news.assert_called_once_with("apple", 10)
    
    async def test_get_user_preferences(self, agent_wrapper):
        """Test getting user preferences."""
        agent_wrapper.db.get_user_preferences.return_value = {
            "preferred_topics": ["technology"],
            "watchlist_stocks": ["AAPL"]
        }
        
        result = await agent_wrapper.get_user_preferences("test-user")
        
        assert result["preferred_topics"] == ["technology"]
        assert result["watchlist_stocks"] == ["AAPL"]
        agent_wrapper.db.get_user_preferences.assert_called_once_with("test-user")
    
    async def test_get_user_preferences_with_cache(self, agent_wrapper):
        """Test getting user preferences with cached data."""
        cached_prefs = {"preferred_topics": ["technology"]}
        agent_wrapper.cache.get.return_value = cached_prefs
        
        result = await agent_wrapper.get_user_preferences("test-user")
        
        assert result == cached_prefs
        agent_wrapper.db.get_user_preferences.assert_not_called()
    
    async def test_update_user_preferences(self, agent_wrapper):
        """Test updating user preferences."""
        agent_wrapper.db.update_user_preferences.return_value = True
        
        result = await agent_wrapper.update_user_preferences(
            "test-user",
            {"preferred_topics": ["technology", "finance"]}
        )
        
        assert result is True
        agent_wrapper.db.update_user_preferences.assert_called_once()
        agent_wrapper.cache.delete.assert_called_once()
    
    async def test_error_handling_text_command(self, agent_wrapper):
        """Test error handling in text command processing."""
        with patch.object(agent_wrapper, 'agent') as mock_agent:
            mock_agent.get_response.side_effect = Exception("Test error")
            
            result = await agent_wrapper.process_text_command(
                command="test command",
                user_id="test-user",
                session_id="test-session"
            )
            
            assert result["response_type"] == "error"
            assert "error" in result["response_text"].lower()
    
    async def test_error_handling_voice_command(self, agent_wrapper):
        """Test error handling in voice command processing."""
        with patch.object(agent_wrapper, 'process_text_command') as mock_process:
            mock_process.side_effect = Exception("Test error")
            
            result = await agent_wrapper.process_voice_command(
                command="test command",
                user_id="test-user",
                session_id="test-session"
            )
            
            assert result["response_type"] == "error"
            assert "error" in result["response_text"].lower()


class TestMockNewsAgent:
    """Test mock news agent functionality."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock news agent instance."""
        return MockNewsAgent()
    
    async def test_get_response_news_command(self, mock_agent):
        """Test mock agent response for news command."""
        result = await mock_agent.get_response("tell me the news")
        
        assert "headlines" in result.lower()
        assert "technology" in result.lower()
    
    async def test_get_response_stock_command(self, mock_agent):
        """Test mock agent response for stock command."""
        result = await mock_agent.get_response("what's the stock price")
        
        assert "market data" in result.lower()
        assert "s&p" in result.lower()
    
    async def test_get_response_tell_me_more(self, mock_agent):
        """Test mock agent response for tell me more command."""
        result = await mock_agent.get_response("tell me more")
        
        assert "more details" in result.lower()
        assert "specify" in result.lower()
    
    async def test_get_response_help(self, mock_agent):
        """Test mock agent response for help command."""
        result = await mock_agent.get_response("help")
        
        assert "help" in result.lower()
        assert "news" in result.lower()
        assert "stock" in result.lower()
    
    async def test_get_response_generic(self, mock_agent):
        """Test mock agent response for generic command."""
        result = await mock_agent.get_response("random command")
        
        assert "understand" in result.lower()
        assert "random command" in result


class TestMockMemory:
    """Test mock memory functionality."""
    
    @pytest.fixture
    def mock_memory(self):
        """Create mock memory instance."""
        return MockMemory()
    
    def test_add_context(self, mock_memory):
        """Test adding context to mock memory."""
        mock_memory.add_context(
            user_input="test input",
            agent_response="test response",
            news_items=[{"id": "news-1"}],
            topic="technology"
        )
        
        assert len(mock_memory.context_history) == 1
        assert mock_memory.context_history[0]["user_input"] == "test input"
        assert mock_memory.context_history[0]["agent_response"] == "test response"
        assert mock_memory.context_history[0]["topic"] == "technology"
    
    def test_get_deep_dive_context(self, mock_memory):
        """Test getting deep dive context from mock memory."""
        result = mock_memory.get_deep_dive_context("tell me more")
        
        assert result is None  # Mock always returns None
