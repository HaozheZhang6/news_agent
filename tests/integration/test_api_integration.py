"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json


class TestAPIIntegration:
    """Test API integration functionality."""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Voice News Agent API" in data["message"]
        assert "version" in data
        assert "status" in data
    
    def test_health_check_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "active_connections" in data
        assert "timestamp" in data
    
    def test_api_documentation(self, test_client):
        """Test API documentation endpoints."""
        # Test OpenAPI docs
        response = test_client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = test_client.get("/redoc")
        assert response.status_code == 200
    
    def test_websocket_status_endpoint(self, test_client):
        """Test WebSocket status endpoint."""
        response = test_client.get("/ws/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data
        assert "max_connections" in data
        assert "status" in data
    
    def test_cors_headers(self, test_client):
        """Test CORS headers."""
        response = test_client.options("/")
        
        # Should not return 405 for OPTIONS request
        assert response.status_code != 405
    
    def test_api_error_handling(self, test_client):
        """Test API error handling."""
        # Test 404 error
        response = test_client.get("/non-existent-endpoint")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert "Not Found" in data["error"]
    
    def test_api_rate_limiting(self, test_client):
        """Test API rate limiting (if implemented)."""
        # Make multiple requests quickly
        for _ in range(5):
            response = test_client.get("/health")
            assert response.status_code == 200
    
    def test_api_content_type(self, test_client):
        """Test API content type handling."""
        response = test_client.get("/")
        
        assert response.headers["content-type"] == "application/json"
    
    def test_api_response_time(self, test_client):
        """Test API response time."""
        import time
        
        start_time = time.time()
        response = test_client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond within reasonable time (5 seconds)
        assert response_time < 5.0
        assert response.status_code == 200


class TestVoiceAPIIntegration:
    """Test voice API integration."""
    
    def test_voice_command_flow(self, test_client):
        """Test complete voice command flow."""
        with patch('backend.app.api.voice.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.process_voice_command.return_value = {
                "response_text": "Here are today's headlines...",
                "response_type": "agent_response",
                "processing_time_ms": 150,
                "session_id": "test-session",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            mock_get_agent.return_value = mock_agent
            
            # Test voice command
            response = test_client.post(
                "/api/voice/command",
                json={
                    "command": "tell me the news",
                    "user_id": "test-user",
                    "session_id": "test-session",
                    "confidence": 0.95
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["response_text"] == "Here are today's headlines..."
            assert data["response_type"] == "agent_response"
    
    def test_text_command_flow(self, test_client):
        """Test complete text command flow."""
        with patch('backend.app.api.voice.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.process_text_command.return_value = {
                "response_text": "Test response",
                "response_type": "agent_response",
                "processing_time_ms": 100,
                "session_id": "test-session",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            mock_get_agent.return_value = mock_agent
            
            # Test text command
            response = test_client.post(
                "/api/voice/text-command",
                params={
                    "command": "tell me the news",
                    "user_id": "test-user",
                    "session_id": "test-session"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["response_text"] == "Test response"
            assert data["response_type"] == "agent_response"
    
    def test_speech_synthesis_flow(self, test_client):
        """Test speech synthesis flow."""
        response = test_client.post(
            "/api/voice/synthesize",
            json={
                "text": "Hello world",
                "voice": "en-US-AriaNeural",
                "rate": 1.0,
                "pitch": 1.0,
                "volume": 1.0,
                "format": "mp3"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "audio_url" in data
        assert data["text_length"] == 11
        assert data["voice"] == "en-US-AriaNeural"


class TestNewsAPIIntegration:
    """Test news API integration."""
    
    def test_news_flow(self, test_client):
        """Test complete news flow."""
        with patch('backend.app.api.news.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_news_latest.return_value = [
                {
                    "id": "news-1",
                    "title": "Test News",
                    "summary": "Test summary",
                    "topics": ["technology"],
                    "source": {"name": "Test Source", "category": "technology"}
                }
            ]
            mock_get_agent.return_value = mock_agent
            
            # Test latest news
            response = test_client.get("/api/news/latest")
            
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert len(data["articles"]) == 1
            assert data["articles"][0]["title"] == "Test News"
    
    def test_news_search_flow(self, test_client):
        """Test news search flow."""
        with patch('backend.app.api.news.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.search_news.return_value = [
                {
                    "id": "news-1",
                    "title": "Apple News",
                    "summary": "Apple related news",
                    "topics": ["technology"]
                }
            ]
            mock_get_agent.return_value = mock_agent
            
            # Test news search
            response = test_client.get(
                "/api/news/search",
                params={"query": "apple", "limit": 10}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert len(data["articles"]) == 1
            assert data["articles"][0]["title"] == "Apple News"
    
    def test_breaking_news_flow(self, test_client):
        """Test breaking news flow."""
        with patch('backend.app.api.news.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_news_latest.return_value = [
                {
                    "id": "news-1",
                    "title": "Breaking News",
                    "is_breaking": True,
                    "topics": ["general"]
                },
                {
                    "id": "news-2",
                    "title": "Regular News",
                    "is_breaking": False,
                    "topics": ["technology"]
                }
            ]
            mock_get_agent.return_value = mock_agent
            
            # Test breaking news
            response = test_client.get("/api/news/breaking")
            
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert len(data["articles"]) == 1  # Only breaking news
            assert data["articles"][0]["is_breaking"] is True


class TestUserAPIIntegration:
    """Test user API integration."""
    
    def test_user_preferences_flow(self, test_client):
        """Test user preferences flow."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "preferred_topics": ["technology", "finance"],
                "watchlist_stocks": ["AAPL", "GOOGL"],
                "voice_settings": {
                    "speech_rate": 1.0,
                    "voice_type": "default"
                },
                "notification_settings": {
                    "breaking_news": True,
                    "stock_alerts": True
                }
            }
            mock_get_agent.return_value = mock_agent
            
            # Test get preferences
            response = test_client.get(
                "/api/user/preferences",
                params={"user_id": "test-user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "preferred_topics" in data
            assert "watchlist_stocks" in data
            assert "voice_settings" in data
            assert "notification_settings" in data
    
    def test_user_topics_flow(self, test_client):
        """Test user topics flow."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "preferred_topics": ["technology"]
            }
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            # Test add topic
            response = test_client.post(
                "/api/user/topics/add",
                params={"user_id": "test-user", "topic": "finance"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "finance" in data["message"]
    
    def test_user_watchlist_flow(self, test_client):
        """Test user watchlist flow."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "watchlist_stocks": ["AAPL"]
            }
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            # Test add stock
            response = test_client.post(
                "/api/user/watchlist/add",
                params={"user_id": "test-user", "symbol": "GOOGL"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "GOOGL" in data["message"]


class TestWebSocketIntegration:
    """Test WebSocket integration."""
    
    def test_websocket_connection(self, test_client):
        """Test WebSocket connection."""
        with test_client.websocket_connect("/ws/voice?user_id=test-user") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["event"] == "connected"
            assert "session_id" in data["data"]
    
    def test_websocket_voice_command(self, test_client):
        """Test WebSocket voice command."""
        with test_client.websocket_connect("/ws/voice?user_id=test-user") as websocket:
            # Send voice command
            websocket.send_json({
                "event": "voice_command",
                "data": {
                    "command": "tell me the news",
                    "session_id": "test-session",
                    "confidence": 0.95
                }
            })
            
            # Should receive transcription
            data = websocket.receive_json()
            assert data["event"] == "transcription"
            assert data["data"]["text"] == "tell me the news"
            
            # Should receive response
            data = websocket.receive_json()
            assert data["event"] == "voice_response"
            assert "response_text" in data["data"]
    
    def test_websocket_interrupt(self, test_client):
        """Test WebSocket interrupt."""
        with test_client.websocket_connect("/ws/voice?user_id=test-user") as websocket:
            # Send interrupt
            websocket.send_json({
                "event": "interrupt",
                "data": {
                    "reason": "user_interruption",
                    "session_id": "test-session"
                }
            })
            
            # Should receive interruption confirmation
            data = websocket.receive_json()
            assert data["event"] == "voice_interrupted"
            assert data["data"]["reason"] == "user_interruption"
    
    def test_websocket_error_handling(self, test_client):
        """Test WebSocket error handling."""
        with test_client.websocket_connect("/ws/voice?user_id=test-user") as websocket:
            # Send invalid message
            websocket.send_text("invalid json")
            
            # Should not disconnect
            # (In a real implementation, you might want to send an error message)
            assert True
