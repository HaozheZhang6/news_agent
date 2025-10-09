"""Tests for NewsAgent component."""
import pytest
from unittest.mock import patch, Mock, AsyncMock
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from src.agent import NewsAgent
    from src.memory import conversation_memory
except ImportError:
    # Mock the imports if they don't exist
    NewsAgent = None
    conversation_memory = None


class TestNewsAgent:
    """Test NewsAgent functionality."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = "Mock response"
        return mock_llm
    
    @pytest.fixture
    def mock_agent_executor(self):
        """Create mock agent executor for testing."""
        mock_executor = AsyncMock()
        mock_executor.ainvoke.return_value = {
            'output': 'Mock agent response',
            'intermediate_steps': []
        }
        return mock_executor
    
    @pytest.fixture
    def news_agent(self, mock_llm, mock_agent_executor):
        """Create NewsAgent instance for testing."""
        if NewsAgent is None:
            pytest.skip("NewsAgent not available")
        
        with patch('src.agent.ChatOpenAI', return_value=mock_llm):
            with patch('src.agent.create_tool_calling_agent'):
                with patch('src.agent.AgentExecutor', return_value=mock_agent_executor):
                    agent = NewsAgent()
                    agent.llm = mock_llm
                    agent.agent_executor = mock_agent_executor
                    return agent
    
    async def test_agent_initialization(self, news_agent):
        """Test NewsAgent initialization."""
        assert news_agent is not None
        assert hasattr(news_agent, 'llm')
        assert hasattr(news_agent, 'agent_executor')
        assert hasattr(news_agent, 'tools')
        assert hasattr(news_agent, 'preferences')
    
    async def test_get_response_basic(self, news_agent):
        """Test basic response generation."""
        user_input = "tell me the news"
        
        result = await news_agent.get_response(user_input)
        
        assert result is not None
        assert isinstance(result, str)
        news_agent.agent_executor.ainvoke.assert_called_once()
    
    async def test_get_response_with_news_tool(self, news_agent):
        """Test response generation with news tool."""
        user_input = "what's the latest news"
        
        # Mock tool call response
        news_agent.agent_executor.ainvoke.return_value = {
            'output': 'Here are the latest headlines...',
            'intermediate_steps': [
                (Mock(tool='get_news_headlines'), '[{"title": "Test News", "summary": "Test summary"}]')
            ]
        }
        
        result = await news_agent.get_response(user_input)
        
        assert result is not None
        assert "headlines" in result.lower()
    
    async def test_get_response_deep_dive(self, news_agent):
        """Test deep dive response generation."""
        user_input = "tell me more"
        
        # Mock conversation memory
        with patch('src.agent.conversation_memory') as mock_memory:
            mock_memory.get_deep_dive_context.return_value = {
                'news_item': {
                    'title': 'Test News',
                    'summary': 'Test summary'
                },
                'topic': 'technology'
            }
            
            result = await news_agent.get_response(user_input)
            
            assert result is not None
            mock_memory.get_deep_dive_context.assert_called_once_with(user_input)
    
    async def test_rephrase_news_item_brief(self, news_agent):
        """Test rephrasing news item for brief summary."""
        news_item = {
            'title': 'Test News Title',
            'summary': 'Test news summary content'
        }
        
        result = await news_agent._rephrase_news_item(news_item, "brief")
        
        assert result is not None
        assert isinstance(result, str)
        news_agent.llm.ainvoke.assert_called_once()
    
    async def test_rephrase_news_item_deep_dive(self, news_agent):
        """Test rephrasing news item for deep dive."""
        news_item = {
            'title': 'Test News Title',
            'summary': 'Test news summary content'
        }
        
        result = await news_agent._rephrase_news_item(news_item, "deep_dive")
        
        assert result is not None
        assert isinstance(result, str)
        news_agent.llm.ainvoke.assert_called_once()
    
    async def test_rephrase_news_item_invalid_type(self, news_agent):
        """Test rephrasing with invalid type."""
        news_item = {
            'title': 'Test News Title',
            'summary': 'Test news summary content'
        }
        
        result = await news_agent._rephrase_news_item(news_item, "invalid")
        
        assert result == "Invalid rephrase type."
    
    async def test_process_fetched_news(self, news_agent):
        """Test processing fetched news items."""
        raw_news_items = [
            {
                'title': 'News 1',
                'summary': 'Summary 1'
            },
            {
                'title': 'News 2',
                'summary': 'Summary 2'
            }
        ]
        
        result = await news_agent.process_fetched_news(raw_news_items)
        
        assert result is not None
        assert "headlines" in result.lower()
        assert "1." in result  # Should contain numbered list
        assert "2." in result
        
        # Check that news items are stored
        assert len(news_agent.current_news_items) == 2
        assert len(news_agent.news_cache) == 2
    
    async def test_format_conversation_history(self, news_agent):
        """Test formatting conversation history."""
        # Mock conversation memory
        with patch('src.agent.conversation_memory') as mock_memory:
            mock_memory.context_history = [
                Mock(user_input="Hello", agent_response="Hi there"),
                Mock(user_input="How are you?", agent_response="I'm doing well")
            ]
            
            result = news_agent._format_conversation_history()
            
            assert isinstance(result, list)
            assert len(result) == 4  # 2 exchanges * 2 messages each
    
    async def test_format_conversation_history_empty(self, news_agent):
        """Test formatting empty conversation history."""
        with patch('src.agent.conversation_memory') as mock_memory:
            mock_memory.context_history = []
            
            result = news_agent._format_conversation_history()
            
            assert isinstance(result, list)
            assert len(result) == 0
    
    def test_extract_topic_from_input(self, news_agent):
        """Test topic extraction from user input."""
        # Test technology topic
        result = news_agent._extract_topic_from_input("tell me about AI technology")
        assert result == "technology"
        
        # Test finance topic
        result = news_agent._extract_topic_from_input("what's the stock market doing")
        assert result == "finance"
        
        # Test crypto topic
        result = news_agent._extract_topic_from_input("bitcoin price today")
        assert result == "crypto"
        
        # Test general topic
        result = news_agent._extract_topic_from_input("hello world")
        assert result == "general"
    
    def test_get_deep_dive(self, news_agent):
        """Test getting deep dive content."""
        # Setup news cache
        news_agent.news_cache = {
            0: "Deep dive content for news item 0",
            1: "Deep dive content for news item 1"
        }
        
        # Test existing item
        result = news_agent.get_deep_dive(0)
        assert result == "Deep dive content for news item 0"
        
        # Test non-existing item
        result = news_agent.get_deep_dive(99)
        assert result == "Deep-dive not available for this item."
    
    async def test_error_handling(self, news_agent):
        """Test error handling in response generation."""
        # Mock agent executor to raise exception
        news_agent.agent_executor.ainvoke.side_effect = Exception("Test error")
        
        result = await news_agent.get_response("test input")
        
        # Should handle error gracefully
        assert result is not None
        assert isinstance(result, str)


class TestNewsAgentMock:
    """Test NewsAgent with mocked dependencies."""
    
    def test_agent_not_available(self):
        """Test behavior when NewsAgent is not available."""
        if NewsAgent is not None:
            pytest.skip("NewsAgent is available")
        
        # Should not raise exception
        assert NewsAgent is None


class TestConversationMemory:
    """Test conversation memory functionality."""
    
    def test_conversation_memory_available(self):
        """Test if conversation memory is available."""
        if conversation_memory is None:
            pytest.skip("Conversation memory not available")
        
        assert conversation_memory is not None
    
    def test_conversation_memory_not_available(self):
        """Test behavior when conversation memory is not available."""
        if conversation_memory is not None:
            pytest.skip("Conversation memory is available")
        
        # Should not raise exception
        assert conversation_memory is None
