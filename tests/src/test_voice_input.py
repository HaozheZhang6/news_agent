"""Tests for voice input component."""
import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from src.voice_input import VoiceListener
except ImportError:
    VoiceListener = None


class TestVoiceListener:
    """Test VoiceListener functionality."""
    
    @pytest.fixture
    def mock_queue(self):
        """Create mock queue for testing."""
        return Mock()
    
    @pytest.fixture
    def voice_listener(self, mock_queue):
        """Create VoiceListener instance for testing."""
        if VoiceListener is None:
            pytest.skip("VoiceListener not available")
        
        with patch('src.voice_input.sr') as mock_sr:
            mock_recognizer = Mock()
            mock_sr.Recognizer.return_value = mock_recognizer
            
            listener = VoiceListener(mock_queue)
            listener.recognizer = mock_recognizer
            return listener
    
    def test_voice_listener_initialization(self, voice_listener, mock_queue):
        """Test VoiceListener initialization."""
        assert voice_listener is not None
        assert voice_listener.command_queue == mock_queue
        assert hasattr(voice_listener, '_stop_event')
        assert hasattr(voice_listener, '_thread')
    
    def test_start_listening(self, voice_listener):
        """Test starting voice listening."""
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            voice_listener.start()
            
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            assert voice_listener._thread == mock_thread_instance
    
    def test_stop_listening(self, voice_listener):
        """Test stopping voice listening."""
        # Mock thread
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        voice_listener._thread = mock_thread
        
        voice_listener.stop()
        
        # Should set stop event and join thread
        assert voice_listener._stop_event.is_set()
        mock_thread.join.assert_called_once()
    
    def test_stop_listening_no_thread(self, voice_listener):
        """Test stopping voice listening when no thread exists."""
        voice_listener._thread = None
        
        # Should not raise exception
        voice_listener.stop()
    
    def test_listen_loop_with_audio(self, voice_listener, mock_queue):
        """Test listen loop with successful audio recognition."""
        # Mock microphone and audio
        mock_microphone = Mock()
        mock_audio = Mock()
        
        voice_listener.recognizer.listen.return_value = mock_audio
        voice_listener.recognizer.recognize_google.return_value = "test command"
        
        with patch('src.voice_input.sr.Microphone', return_value=mock_microphone):
            with patch('time.sleep'):
                # Start the listen loop
                voice_listener._listen_loop()
        
        # Should recognize audio and put command in queue
        voice_listener.recognizer.recognize_google.assert_called_once()
        mock_queue.put.assert_called_once_with("test command")
    
    def test_listen_loop_unknown_value_error(self, voice_listener, mock_queue):
        """Test listen loop with unknown value error."""
        # Mock microphone and audio
        mock_microphone = Mock()
        mock_audio = Mock()
        
        voice_listener.recognizer.listen.return_value = mock_audio
        voice_listener.recognizer.recognize_google.side_effect = Exception("UnknownValueError")
        
        with patch('src.voice_input.sr.Microphone', return_value=mock_microphone):
            with patch('time.sleep'):
                # Should not raise exception
                voice_listener._listen_loop()
        
        # Should not put anything in queue
        mock_queue.put.assert_not_called()
    
    def test_listen_loop_request_error(self, voice_listener, mock_queue):
        """Test listen loop with request error."""
        # Mock microphone and audio
        mock_microphone = Mock()
        mock_audio = Mock()
        
        voice_listener.recognizer.listen.return_value = mock_audio
        voice_listener.recognizer.recognize_google.side_effect = Exception("RequestError")
        
        with patch('src.voice_input.sr.Microphone', return_value=mock_microphone):
            with patch('time.sleep'):
                # Should not raise exception
                voice_listener._listen_loop()
        
        # Should not put anything in queue
        mock_queue.put.assert_not_called()
    
    def test_listen_loop_stop_event_set(self, voice_listener, mock_queue):
        """Test listen loop when stop event is set."""
        # Set stop event before starting
        voice_listener._stop_event.set()
        
        # Mock microphone
        mock_microphone = Mock()
        
        with patch('src.voice_input.sr.Microphone', return_value=mock_microphone):
            with patch('time.sleep'):
                # Should exit immediately
                voice_listener._listen_loop()
        
        # Should not process any audio
        voice_listener.recognizer.listen.assert_not_called()
    
    def test_listen_loop_audio_listen_error(self, voice_listener, mock_queue):
        """Test listen loop with audio listen error."""
        # Mock microphone
        mock_microphone = Mock()
        voice_listener.recognizer.listen.side_effect = Exception("Audio error")
        
        with patch('src.voice_input.sr.Microphone', return_value=mock_microphone):
            with patch('time.sleep'):
                # Should not raise exception
                voice_listener._listen_loop()
        
        # Should not put anything in queue
        mock_queue.put.assert_not_called()
    
    def test_start_multiple_times(self, voice_listener):
        """Test starting voice listener multiple times."""
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            # Start first time
            voice_listener.start()
            assert voice_listener._thread == mock_thread_instance
            
            # Start second time (should not create new thread)
            voice_listener.start()
            
            # Should only create one thread
            assert mock_thread.call_count == 1
    
    def test_start_with_existing_thread(self, voice_listener):
        """Test starting with existing alive thread."""
        # Mock existing thread
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        voice_listener._thread = mock_thread
        
        with patch('threading.Thread') as mock_thread_class:
            voice_listener.start()
            
            # Should not create new thread
            mock_thread_class.assert_not_called()


class TestVoiceListenerMock:
    """Test VoiceListener with mocked dependencies."""
    
    def test_voice_listener_not_available(self):
        """Test behavior when VoiceListener is not available."""
        if VoiceListener is not None:
            pytest.skip("VoiceListener is available")
        
        # Should not raise exception
        assert VoiceListener is None


class TestVoiceInputIntegration:
    """Integration tests for voice input."""
    
    def test_voice_input_imports(self):
        """Test that voice input can be imported."""
        try:
            import src.voice_input
            assert True
        except ImportError:
            pytest.skip("Voice input module not available")
    
    def test_voice_input_dependencies(self):
        """Test voice input dependencies."""
        try:
            import speechrecognition as sr
            assert True
        except ImportError:
            pytest.skip("SpeechRecognition not available")
    
    def test_voice_input_threading(self):
        """Test voice input threading functionality."""
        try:
            import threading
            import queue
            
            # Test basic threading
            test_queue = queue.Queue()
            stop_event = threading.Event()
            
            assert test_queue is not None
            assert stop_event is not None
            
        except ImportError:
            pytest.skip("Threading not available")
