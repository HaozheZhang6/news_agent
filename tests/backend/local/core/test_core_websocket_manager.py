"""Tests for WebSocket manager core component."""
import pytest
import json
from unittest.mock import patch, AsyncMock, Mock
from backend.app.core.websocket_manager import WebSocketManager


class TestWebSocketManager:
    """Test WebSocket manager functionality."""
    
    @pytest.fixture
    async def ws_manager(self, mock_database, mock_cache, mock_agent):
        """Create WebSocket manager instance for testing."""
        manager = WebSocketManager()
        manager.db = mock_database
        manager.cache = mock_cache
        manager.agent = mock_agent
        manager._initialized = True
        return manager
    
    async def test_initialize(self, mock_database, mock_cache, mock_agent):
        """Test WebSocket manager initialization."""
        manager = WebSocketManager()
        
        with patch('backend.app.core.websocket_manager.get_database', return_value=mock_database):
            with patch('backend.app.core.websocket_manager.get_cache', return_value=mock_cache):
                with patch('backend.app.core.websocket_manager.get_agent', return_value=mock_agent):
                    await manager.initialize()
        
        assert manager._initialized is True
        assert manager.db == mock_database
        assert manager.cache == mock_cache
        assert manager.agent == mock_agent
    
    async def test_connect(self, ws_manager, mock_websocket):
        """Test WebSocket connection."""
        user_id = "test-user"
        
        with patch.object(ws_manager.db, 'create_conversation_session') as mock_create_session:
            mock_create_session.return_value = {"id": "session-123"}
            
            session_id = await ws_manager.connect(mock_websocket, user_id)
        
        assert session_id is not None
        assert session_id in ws_manager.active_connections
        assert session_id in ws_manager.session_data
        assert ws_manager.user_sessions[user_id] == session_id
        
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_text.assert_called_once()
        
        # Check welcome message was sent
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        assert message["event"] == "connected"
        assert message["data"]["session_id"] == session_id
    
    async def test_disconnect(self, ws_manager, mock_websocket):
        """Test WebSocket disconnection."""
        user_id = "test-user"
        session_id = "test-session"
        
        # Setup active connection
        ws_manager.active_connections[session_id] = mock_websocket
        ws_manager.user_sessions[user_id] = session_id
        ws_manager.session_data[session_id] = {
            "user_id": user_id,
            "websocket": mock_websocket,
            "is_active": True
        }
        
        await ws_manager.disconnect(session_id)
        
        assert session_id not in ws_manager.active_connections
        assert user_id not in ws_manager.user_sessions
        assert session_id not in ws_manager.session_data
    
    async def test_send_message(self, ws_manager, mock_websocket):
        """Test sending message to WebSocket."""
        session_id = "test-session"
        ws_manager.active_connections[session_id] = mock_websocket
        
        message = {"event": "test", "data": {"message": "test"}}
        await ws_manager.send_message(session_id, message)
        
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        sent_message = json.loads(call_args)
        assert sent_message == message
    
    async def test_send_message_disconnected(self, ws_manager):
        """Test sending message to disconnected WebSocket."""
        session_id = "non-existent-session"
        
        # Should not raise exception
        await ws_manager.send_message(session_id, {"event": "test"})
    
    async def test_broadcast_message(self, ws_manager, mock_websocket):
        """Test broadcasting message to all connections."""
        session_id1 = "session-1"
        session_id2 = "session-2"
        
        ws_manager.active_connections[session_id1] = mock_websocket
        ws_manager.active_connections[session_id2] = mock_websocket
        
        message = {"event": "broadcast", "data": {"message": "broadcast"}}
        await ws_manager.broadcast_message(message)
        
        # Should be called twice (once for each session)
        assert mock_websocket.send_text.call_count == 2
    
    async def test_handle_voice_command(self, ws_manager):
        """Test handling voice command."""
        session_id = "test-session"
        user_id = "test-user"
        
        ws_manager.session_data[session_id] = {
            "user_id": user_id,
            "total_commands": 0
        }
        
        data = {
            "command": "tell me the news",
            "confidence": 0.95
        }
        
        with patch.object(ws_manager, 'send_message') as mock_send:
            await ws_manager.handle_voice_command(session_id, data)
        
        # Should send transcription and response messages
        assert mock_send.call_count == 2
        
        # Check transcription message
        transcription_call = mock_send.call_args_list[0][0]
        transcription_message = transcription_call[1]
        assert transcription_message["event"] == "transcription"
        assert transcription_message["data"]["text"] == "tell me the news"
        
        # Check response message
        response_call = mock_send.call_args_list[1][0]
        response_message = response_call[1]
        assert response_message["event"] == "voice_response"
        assert "response_text" in response_message["data"]
    
    async def test_handle_voice_command_invalid_session(self, ws_manager):
        """Test handling voice command with invalid session."""
        session_id = "invalid-session"
        data = {"command": "test"}
        
        with patch.object(ws_manager, 'send_message') as mock_send:
            await ws_manager.handle_voice_command(session_id, data)
        
        # Should send error message
        mock_send.assert_called_once()
        error_message = mock_send.call_args[0][1]
        assert error_message["event"] == "error"
        assert error_message["data"]["error_type"] == "invalid_session"
    
    async def test_handle_voice_data(self, ws_manager):
        """Test handling voice data."""
        session_id = "test-session"
        user_id = "test-user"
        
        ws_manager.session_data[session_id] = {
            "user_id": user_id
        }
        
        data = {
            "audio_chunk": "base64_audio_data"
        }
        
        with patch.object(ws_manager, 'send_message') as mock_send:
            await ws_manager.handle_voice_data(session_id, data)
        
        # Should send acknowledgment message
        mock_send.assert_called_once()
        ack_message = mock_send.call_args[0][1]
        assert ack_message["event"] == "audio_received"
    
    async def test_handle_interrupt(self, ws_manager):
        """Test handling interruption."""
        session_id = "test-session"
        
        ws_manager.session_data[session_id] = {
            "total_interruptions": 0
        }
        
        data = {
            "reason": "user_interruption"
        }
        
        with patch.object(ws_manager, 'send_message') as mock_send:
            await ws_manager.handle_interrupt(session_id, data)
        
        # Should increment interruption count
        assert ws_manager.session_data[session_id]["total_interruptions"] == 1
        
        # Should send interruption message
        mock_send.assert_called_once()
        interrupt_message = mock_send.call_args[0][1]
        assert interrupt_message["event"] == "voice_interrupted"
        assert interrupt_message["data"]["reason"] == "user_interruption"
    
    async def test_handle_start_listening(self, ws_manager):
        """Test handling start listening command."""
        session_id = "test-session"
        
        with patch.object(ws_manager, 'send_message') as mock_send:
            await ws_manager.handle_start_listening(session_id, {})
        
        # Should send listening started message
        mock_send.assert_called_once()
        message = mock_send.call_args[0][1]
        assert message["event"] == "listening_started"
    
    async def test_handle_stop_listening(self, ws_manager):
        """Test handling stop listening command."""
        session_id = "test-session"
        
        with patch.object(ws_manager, 'send_message') as mock_send:
            await ws_manager.handle_stop_listening(session_id, {})
        
        # Should send listening stopped message
        mock_send.assert_called_once()
        message = mock_send.call_args[0][1]
        assert message["event"] == "listening_stopped"
    
    async def test_process_message_voice_command(self, ws_manager, mock_websocket):
        """Test processing voice command message."""
        session_id = "test-session"
        message = json.dumps({
            "event": "voice_command",
            "data": {
                "command": "tell me the news",
                "session_id": session_id,
                "confidence": 0.95
            }
        })
        
        with patch.object(ws_manager, 'handle_voice_command') as mock_handle:
            await ws_manager.process_message(mock_websocket, message)
        
        mock_handle.assert_called_once()
    
    async def test_process_message_voice_data(self, ws_manager, mock_websocket):
        """Test processing voice data message."""
        session_id = "test-session"
        message = json.dumps({
            "event": "voice_data",
            "data": {
                "audio_chunk": "base64_data",
                "session_id": session_id
            }
        })
        
        with patch.object(ws_manager, 'handle_voice_data') as mock_handle:
            await ws_manager.process_message(mock_websocket, message)
        
        mock_handle.assert_called_once()
    
    async def test_process_message_interrupt(self, ws_manager, mock_websocket):
        """Test processing interrupt message."""
        session_id = "test-session"
        message = json.dumps({
            "event": "interrupt",
            "data": {
                "reason": "user_interruption",
                "session_id": session_id
            }
        })
        
        with patch.object(ws_manager, 'handle_interrupt') as mock_handle:
            await ws_manager.process_message(mock_websocket, message)
        
        mock_handle.assert_called_once()
    
    async def test_process_message_unknown_event(self, ws_manager, mock_websocket):
        """Test processing unknown event message."""
        message = json.dumps({
            "event": "unknown_event",
            "data": {"session_id": "test-session"}
        })
        
        # Should not raise exception
        await ws_manager.process_message(mock_websocket, message)
    
    async def test_process_message_invalid_json(self, ws_manager, mock_websocket):
        """Test processing invalid JSON message."""
        message = "invalid json"
        
        # Should not raise exception
        await ws_manager.process_message(mock_websocket, message)
    
    def test_get_active_connections_count(self, ws_manager):
        """Test getting active connections count."""
        ws_manager.active_connections["session-1"] = Mock()
        ws_manager.active_connections["session-2"] = Mock()
        
        count = ws_manager.get_active_connections_count()
        assert count == 2
    
    def test_get_session_info(self, ws_manager):
        """Test getting session information."""
        session_id = "test-session"
        session_data = {"user_id": "test-user", "is_active": True}
        
        ws_manager.session_data[session_id] = session_data
        
        info = ws_manager.get_session_info(session_id)
        assert info == session_data
        
        # Test non-existent session
        info = ws_manager.get_session_info("non-existent")
        assert info is None
    
    def test_get_user_session(self, ws_manager):
        """Test getting user session ID."""
        user_id = "test-user"
        session_id = "test-session"
        
        ws_manager.user_sessions[user_id] = session_id
        
        result = ws_manager.get_user_session(user_id)
        assert result == session_id
        
        # Test non-existent user
        result = ws_manager.get_user_session("non-existent")
        assert result is None
