"""Pytest configuration and fixtures for Voice News Agent tests."""
import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

# Set test environment variables
os.environ.update({
    'ENVIRONMENT': 'test',
    'DEBUG': 'true',
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_KEY': 'test-key',
    'SUPABASE_SERVICE_KEY': 'test-service-key',
    'UPSTASH_REDIS_REST_URL': 'https://test-redis.upstash.io',
    'UPSTASH_REDIS_REST_TOKEN': 'test-token',
    'ZHIPUAI_API_KEY': 'test-zhipuai-key',
    'ALPHAVANTAGE_API_KEY': 'test-alphavantage-key',
    'SECRET_KEY': 'test-secret-key',
    'CORS_ORIGINS': '["http://localhost:3000"]',
    'LOG_LEVEL': 'DEBUG'
})


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database() -> AsyncMock:
    """Mock database for testing."""
    mock_db = AsyncMock()
    mock_db.health_check.return_value = True
    mock_db.get_user.return_value = {
        "id": "test-user",
        "email": "test@example.com",
        "subscription_tier": "free"
    }
    mock_db.get_user_preferences.return_value = {
        "preferred_topics": ["technology", "finance"],
        "watchlist_stocks": ["AAPL", "GOOGL"]
    }
    mock_db.update_user_preferences.return_value = True
    mock_db.create_conversation_session.return_value = {
        "id": "test-session",
        "user_id": "test-user",
        "session_start": "2024-01-01T00:00:00Z",
        "is_active": True
    }
    mock_db.add_conversation_message.return_value = {
        "id": "test-message",
        "session_id": "test-session",
        "user_id": "test-user",
        "message_type": "user_input",
        "content": "test message",
        "created_at": "2024-01-01T00:00:00Z"
    }
    mock_db.get_conversation_messages.return_value = []
    mock_db.get_latest_news.return_value = [
        {
            "id": "news-1",
            "title": "Test News Article",
            "summary": "This is a test news article",
            "published_at": "2024-01-01T00:00:00Z",
            "topics": ["technology"],
            "source": {"name": "Test Source", "category": "technology"}
        }
    ]
    mock_db.search_news.return_value = []
    mock_db.get_stock_data.return_value = {
        "symbol": "AAPL",
        "current_price": 150.0,
        "change_percent": 1.5,
        "last_updated": "2024-01-01T00:00:00Z"
    }
    mock_db.track_user_interaction.return_value = True
    return mock_db


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Mock cache for testing."""
    mock_cache = AsyncMock()
    mock_cache.health_check.return_value = True
    mock_cache.get.return_value = None
    mock_cache.set.return_value = True
    mock_cache.delete.return_value = True
    mock_cache.exists.return_value = False
    mock_cache.get_multiple.return_value = {}
    mock_cache.set_multiple.return_value = True
    return mock_cache


@pytest.fixture
def mock_agent() -> AsyncMock:
    """Mock agent for testing."""
    mock_agent = AsyncMock()
    mock_agent.process_text_command.return_value = {
        "response_text": "Test response",
        "response_type": "agent_response",
        "processing_time_ms": 100,
        "session_id": "test-session",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    mock_agent.process_voice_command.return_value = {
        "response_text": "Test voice response",
        "response_type": "agent_response",
        "processing_time_ms": 150,
        "session_id": "test-session",
        "audio_url": None,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    mock_agent.get_news_latest.return_value = [
        {
            "id": "news-1",
            "title": "Test News",
            "summary": "Test summary",
            "topics": ["technology"]
        }
    ]
    mock_agent.get_stock_data.return_value = {
        "symbol": "AAPL",
        "current_price": 150.0
    }
    mock_agent.search_news.return_value = []
    mock_agent.get_user_preferences.return_value = {
        "preferred_topics": ["technology"],
        "watchlist_stocks": ["AAPL"]
    }
    mock_agent.update_user_preferences.return_value = True
    return mock_agent


@pytest.fixture
def mock_websocket() -> Mock:
    """Mock WebSocket for testing."""
    mock_ws = Mock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "email": "test@example.com",
        "subscription_tier": "free",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "last_active": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_news_data() -> dict:
    """Sample news data for testing."""
    return {
        "id": "news-123",
        "title": "Apple Announces New AI Features",
        "summary": "Apple unveiled new AI capabilities for iOS 18",
        "content": "Full article content here...",
        "url": "https://example.com/news/apple-ai",
        "published_at": "2024-01-01T00:00:00Z",
        "sentiment_score": 0.8,
        "topics": ["technology", "ai"],
        "is_breaking": False,
        "source": {
            "name": "Tech News",
            "category": "technology",
            "reliability_score": 0.9
        }
    }


@pytest.fixture
def sample_stock_data() -> dict:
    """Sample stock data for testing."""
    return {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "current_price": 150.25,
        "change_percent": 1.5,
        "volume": 50000000,
        "market_cap": 2500000000000,
        "last_updated": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_voice_command() -> dict:
    """Sample voice command for testing."""
    return {
        "command": "tell me the news",
        "user_id": "test-user",
        "session_id": "test-session",
        "confidence": 0.95,
        "language": "en-US"
    }


@pytest.fixture
def sample_conversation_session() -> dict:
    """Sample conversation session for testing."""
    return {
        "id": "session-123",
        "user_id": "test-user",
        "session_start": "2024-01-01T00:00:00Z",
        "session_end": None,
        "total_interactions": 0,
        "voice_interruptions": 0,
        "topics_discussed": [],
        "is_active": True
    }


@pytest.fixture
def sample_conversation_message() -> dict:
    """Sample conversation message for testing."""
    return {
        "id": "message-123",
        "session_id": "session-123",
        "user_id": "test-user",
        "message_type": "user_input",
        "content": "tell me the news",
        "audio_url": None,
        "processing_time_ms": 100,
        "confidence_score": 0.95,
        "referenced_news_ids": [],
        "metadata": {},
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def test_client():
    """Test client for FastAPI testing."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    return TestClient(app)


# Async test utilities
@pytest.fixture
async def async_test_client():
    """Async test client for FastAPI testing."""
    from httpx import AsyncClient
    from backend.app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client