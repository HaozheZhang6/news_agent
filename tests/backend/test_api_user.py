"""Tests for user API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestUserAPI:
    """Test user API endpoints."""
    
    def test_get_user_preferences(self, test_client):
        """Test getting user preferences."""
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
            assert data["preferred_topics"] == ["technology", "finance"]
    
    def test_update_user_preferences(self, test_client):
        """Test updating user preferences."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            response = test_client.put(
                "/api/user/preferences",
                params={"user_id": "test-user"},
                json={
                    "preferred_topics": ["technology", "finance", "crypto"],
                    "voice_settings": {
                        "speech_rate": 1.2,
                        "voice_type": "en-US-AriaNeural"
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "successfully" in data["message"]
    
    def test_get_user_topics(self, test_client):
        """Test getting user's preferred topics."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "preferred_topics": ["technology", "finance"]
            }
            mock_get_agent.return_value = mock_agent
            
            response = test_client.get(
                "/api/user/topics",
                params={"user_id": "test-user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "preferred_topics" in data
            assert "available_topics" in data
            assert data["preferred_topics"] == ["technology", "finance"]
            assert len(data["available_topics"]) > 0
    
    def test_add_user_topic(self, test_client):
        """Test adding topic to user preferences."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "preferred_topics": ["technology"]
            }
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post(
                "/api/user/topics/add",
                params={"user_id": "test-user", "topic": "finance"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "finance" in data["message"]
    
    def test_remove_user_topic(self, test_client):
        """Test removing topic from user preferences."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "preferred_topics": ["technology", "finance"]
            }
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            response = test_client.delete(
                "/api/user/topics/finance",
                params={"user_id": "test-user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "removed" in data["message"]
    
    def test_get_user_watchlist(self, test_client):
        """Test getting user's stock watchlist."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "watchlist_stocks": ["AAPL", "GOOGL", "MSFT"]
            }
            mock_get_agent.return_value = mock_agent
            
            response = test_client.get(
                "/api/user/watchlist",
                params={"user_id": "test-user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "watchlist_stocks" in data
            assert data["watchlist_stocks"] == ["AAPL", "GOOGL", "MSFT"]
    
    def test_add_watchlist_stock(self, test_client):
        """Test adding stock to user's watchlist."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "watchlist_stocks": ["AAPL"]
            }
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post(
                "/api/user/watchlist/add",
                params={"user_id": "test-user", "symbol": "GOOGL"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "GOOGL" in data["message"]
    
    def test_remove_watchlist_stock(self, test_client):
        """Test removing stock from user's watchlist."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "watchlist_stocks": ["AAPL", "GOOGL"]
            }
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            response = test_client.delete(
                "/api/user/watchlist/AAPL",
                params={"user_id": "test-user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "removed" in data["message"]
    
    def test_get_user_analytics(self, test_client):
        """Test getting user analytics."""
        response = test_client.get(
            "/api/user/analytics",
            params={"user_id": "test-user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "total_interactions" in data
        assert "successful_interactions" in data
        assert "average_response_time_ms" in data
        assert "most_used_topics" in data
        assert "most_used_commands" in data
        assert "session_count" in data
        assert "total_session_time_minutes" in data
    
    def test_user_health_check(self, test_client):
        """Test user health check endpoint."""
        response = test_client.get("/api/user/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
    
    def test_add_duplicate_topic(self, test_client):
        """Test adding duplicate topic to user preferences."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "preferred_topics": ["technology", "finance"]
            }
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post(
                "/api/user/topics/add",
                params={"user_id": "test-user", "topic": "technology"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            # Should still return success even for duplicate
    
    def test_add_duplicate_stock(self, test_client):
        """Test adding duplicate stock to watchlist."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.return_value = {
                "watchlist_stocks": ["AAPL", "GOOGL"]
            }
            mock_agent.update_user_preferences.return_value = True
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post(
                "/api/user/watchlist/add",
                params={"user_id": "test-user", "symbol": "AAPL"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            # Should still return success even for duplicate
    
    def test_user_api_error_handling(self, test_client):
        """Test error handling in user API."""
        with patch('backend.app.api.user.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_user_preferences.side_effect = Exception("Database error")
            mock_get_agent.return_value = mock_agent
            
            response = test_client.get(
                "/api/user/preferences",
                params={"user_id": "test-user"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"]
