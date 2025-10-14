"""Tests for voice API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestVoiceAPI:
    """Test voice API endpoints."""
    
    def test_voice_command_endpoint(self, test_client):
        """Test voice command processing endpoint."""
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
            assert data["session_id"] == "test-session"
    
    def test_text_command_endpoint(self, test_client):
        """Test text command processing endpoint."""
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
    
    def test_synthesize_speech_endpoint(self, test_client):
        """Test speech synthesis endpoint."""
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
    
    def test_voice_health_check(self, test_client):
        """Test voice health check endpoint."""
        response = test_client.get("/api/voice/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert data["services"]["agent"] == "available"
    
    def test_voice_command_error_handling(self, test_client):
        """Test error handling in voice command endpoint."""
        with patch('backend.app.api.voice.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.process_voice_command.side_effect = Exception("Test error")
            mock_get_agent.return_value = mock_agent
            
            response = test_client.post(
                "/api/voice/command",
                json={
                    "command": "test command",
                    "user_id": "test-user",
                    "session_id": "test-session"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"]
    
    def test_invalid_voice_command_request(self, test_client):
        """Test invalid voice command request."""
        response = test_client.post(
            "/api/voice/command",
            json={
                "command": "",  # Empty command
                "user_id": "test-user",
                "session_id": "test-session"
            }
        )
        
        # Should still process but with empty command
        assert response.status_code == 200
    
    def test_missing_parameters_text_command(self, test_client):
        """Test text command with missing parameters."""
        response = test_client.post(
            "/api/voice/text-command",
            params={
                "command": "test command"
                # Missing user_id and session_id
            }
        )
        
        assert response.status_code == 422  # Validation error
