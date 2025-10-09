"""Tests for news API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestNewsAPI:
    """Test news API endpoints."""
    
    def test_get_latest_news(self, test_client):
        """Test getting latest news."""
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
            
            response = test_client.get("/api/news/latest")
            
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert len(data["articles"]) == 1
            assert data["articles"][0]["title"] == "Test News"
    
    def test_get_latest_news_with_topics(self, test_client):
        """Test getting latest news with topic filter."""
        with patch('backend.app.api.news.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_news_latest.return_value = []
            mock_get_agent.return_value = mock_agent
            
            response = test_client.get(
                "/api/news/latest",
                params={"topics": ["technology", "finance"], "limit": 5}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            mock_agent.get_news_latest.assert_called_once_with(["technology", "finance"], 5)
    
    def test_search_news(self, test_client):
        """Test news search endpoint."""
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
            
            response = test_client.get(
                "/api/news/search",
                params={"query": "apple", "limit": 10}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert len(data["articles"]) == 1
            mock_agent.search_news.assert_called_once_with("apple", 10)
    
    def test_get_news_article(self, test_client):
        """Test getting specific news article."""
        with patch('backend.app.api.news.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.get_news_article.return_value = {
                "id": "news-1",
                "title": "Test Article",
                "summary": "Test summary",
                "content": "Full content"
            }
            mock_get_db.return_value = mock_db
            
            response = test_client.get("/api/news/article/news-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Article"
    
    def test_get_news_article_not_found(self, test_client):
        """Test getting non-existent news article."""
        with patch('backend.app.api.news.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_db.get_news_article.return_value = None
            mock_get_db.return_value = mock_db
            
            response = test_client.get("/api/news/article/non-existent")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    def test_summarize_news(self, test_client):
        """Test news summarization endpoint."""
        response = test_client.post(
            "/api/news/summarize",
            json={
                "article_ids": ["news-1", "news-2"],
                "summary_type": "brief",
                "max_length": 200
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("summary" in item for item in data)
        assert all("article_id" in item for item in data)
    
    def test_get_breaking_news(self, test_client):
        """Test getting breaking news."""
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
            
            response = test_client.get("/api/news/breaking")
            
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert len(data["articles"]) == 1  # Only breaking news
            assert data["articles"][0]["is_breaking"] is True
    
    def test_get_news_topics(self, test_client):
        """Test getting available news topics."""
        response = test_client.get("/api/news/topics")
        
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert "count" in data
        assert len(data["topics"]) > 0
        assert "technology" in data["topics"]
    
    def test_news_health_check(self, test_client):
        """Test news health check endpoint."""
        response = test_client.get("/api/news/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
    
    def test_news_api_error_handling(self, test_client):
        """Test error handling in news API."""
        with patch('backend.app.api.news.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.get_news_latest.side_effect = Exception("Database error")
            mock_get_agent.return_value = mock_agent
            
            response = test_client.get("/api/news/latest")
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"]
    
    def test_search_news_with_filters(self, test_client):
        """Test news search with category and topic filters."""
        with patch('backend.app.api.news.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.search_news.return_value = []
            mock_get_agent.return_value = mock_agent
            
            response = test_client.get(
                "/api/news/search",
                params={
                    "query": "technology",
                    "category": "technology",
                    "topics": ["ai", "software"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
