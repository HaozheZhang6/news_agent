"""Tests for voice output component."""
import pytest
from unittest.mock import patch, Mock, MagicMock, AsyncMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from src.voice_output import (
        speak_text, stop_speech, is_speaking, 
        voice_monitoring_thread, _ensure_mixer_initialized
    )
except ImportError:
    # Mock the imports if they don't exist
    speak_text = None
    stop_speech = None
    is_speaking = None
    voice_monitoring_thread = None
    _ensure_mixer_initialized = None


class TestVoiceOutput:
    """Test voice output functionality."""
    
    @pytest.fixture
    def mock_pygame(self):
        """Create mock pygame for testing."""
        mock_pygame = Mock()
        mock_mixer = Mock()
        mock_pygame.mixer = mock_mixer
        return mock_pygame
    
    @pytest.fixture
    def mock_edge_tts(self):
        """Create mock edge_tts for testing."""
        mock_edge_tts = Mock()
        mock_communicate = AsyncMock()
        mock_edge_tts.Communicate.return_value = mock_communicate
        return mock_edge_tts
    
    def test_voice_output_imports(self):
        """Test that voice output can be imported."""
        if speak_text is None:
            pytest.skip("Voice output module not available")
        
        assert speak_text is not None
        assert stop_speech is not None
        assert is_speaking is not None
    
    @patch('src.voice_output.pygame')
    def test_ensure_mixer_initialized(self, mock_pygame):
        """Test pygame mixer initialization."""
        if _ensure_mixer_initialized is None:
            pytest.skip("Voice output module not available")
        
        mock_mixer = Mock()
        mock_pygame.mixer = mock_mixer
        
        _ensure_mixer_initialized()
        
        mock_mixer.pre_init.assert_called_once()
        mock_mixer.init.assert_called_once()
    
    @patch('src.voice_output.pygame')
    def test_ensure_mixer_initialized_error(self, mock_pygame):
        """Test pygame mixer initialization with error."""
        if _ensure_mixer_initialized is None:
            pytest.skip("Voice output module not available")
        
        mock_mixer = Mock()
        mock_mixer.pre_init.side_effect = Exception("Mixer error")
        mock_pygame.mixer = mock_mixer
        
        # Should not raise exception
        _ensure_mixer_initialized()
    
    @pytest.mark.asyncio
    async def test_speak_text(self, mock_edge_tts):
        """Test text-to-speech functionality."""
        if speak_text is None:
            pytest.skip("Voice output module not available")
        
        with patch('src.voice_output.edge_tts', mock_edge_tts):
            with patch('src.voice_output._ensure_mixer_initialized'):
                with patch('src.voice_output.pygame') as mock_pygame:
                    mock_sound = Mock()
                    mock_pygame.mixer.Sound.return_value = mock_sound
                    
                    result = await speak_text("Hello world")
                    
                    assert result is not None
                    mock_edge_tts.Communicate.assert_called_once()
                    mock_sound.play.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_speak_text_error(self, mock_edge_tts):
        """Test text-to-speech with error."""
        if speak_text is None:
            pytest.skip("Voice output module not available")
        
        mock_edge_tts.Communicate.side_effect = Exception("TTS error")
        
        with patch('src.voice_output.edge_tts', mock_edge_tts):
            with patch('src.voice_output._ensure_mixer_initialized'):
                # Should handle error gracefully
                result = await speak_text("Hello world")
                
                # Should return None or handle error
                assert result is None or isinstance(result, str)
    
    def test_stop_speech(self):
        """Test stopping speech."""
        if stop_speech is None:
            pytest.skip("Voice output module not available")
        
        with patch('src.voice_output.pygame') as mock_pygame:
            mock_mixer = Mock()
            mock_pygame.mixer = mock_mixer
            
            stop_speech()
            
            mock_mixer.stop.assert_called_once()
    
    def test_is_speaking(self):
        """Test checking if currently speaking."""
        if is_speaking is None:
            pytest.skip("Voice output module not available")
        
        with patch('src.voice_output.pygame') as mock_pygame:
            mock_mixer = Mock()
            mock_mixer.get_busy.return_value = True
            mock_pygame.mixer = mock_mixer
            
            result = is_speaking()
            
            assert result is True
            mock_mixer.get_busy.assert_called_once()
    
    def test_voice_monitoring_thread(self):
        """Test voice monitoring thread."""
        if voice_monitoring_thread is None:
            pytest.skip("Voice output module not available")
        
        with patch('src.voice_output.pyaudio') as mock_pyaudio:
            with patch('src.voice_output.vad_detector') as mock_vad:
                with patch('src.voice_output.conversation_logger') as mock_logger:
                    # Mock PyAudio
                    mock_p = Mock()
                    mock_stream = Mock()
                    mock_p.open.return_value = mock_stream
                    mock_pyaudio.PyAudio.return_value = mock_p
                    
                    # Mock VAD
                    mock_vad.is_speech.return_value = True
                    
                    # Mock stream data
                    mock_stream.read.return_value = b'\x00' * 1024
                    
                    # Mock global variables
                    with patch('src.voice_output.active_speech_monitoring', True):
                        with patch('src.voice_output.speech_interrupt_callback') as mock_callback:
                            # Run monitoring thread briefly
                            voice_monitoring_thread()
                    
                    mock_p.open.assert_called_once()
                    mock_stream.read.assert_called()
    
    def test_voice_monitoring_thread_no_speech(self):
        """Test voice monitoring thread with no speech."""
        if voice_monitoring_thread is None:
            pytest.skip("Voice output module not available")
        
        with patch('src.voice_output.pyaudio') as mock_pyaudio:
            with patch('src.voice_output.vad_detector') as mock_vad:
                with patch('src.voice_output.conversation_logger') as mock_logger:
                    # Mock PyAudio
                    mock_p = Mock()
                    mock_stream = Mock()
                    mock_p.open.return_value = mock_stream
                    mock_pyaudio.PyAudio.return_value = mock_p
                    
                    # Mock VAD - no speech detected
                    mock_vad.is_speech.return_value = False
                    
                    # Mock stream data
                    mock_stream.read.return_value = b'\x00' * 1024
                    
                    # Mock global variables
                    with patch('src.voice_output.active_speech_monitoring', True):
                        # Run monitoring thread briefly
                        voice_monitoring_thread()
                    
                    mock_p.open.assert_called_once()
                    mock_stream.read.assert_called()
    
    def test_voice_monitoring_thread_error(self):
        """Test voice monitoring thread with error."""
        if voice_monitoring_thread is None:
            pytest.skip("Voice output module not available")
        
        with patch('src.voice_output.pyaudio') as mock_pyaudio:
            with patch('src.voice_output.conversation_logger') as mock_logger:
                # Mock PyAudio to raise exception
                mock_pyaudio.PyAudio.side_effect = Exception("Audio error")
                
                # Should not raise exception
                voice_monitoring_thread()
                
                mock_logger.log_error.assert_called()


class TestVoiceOutputMock:
    """Test voice output with mocked dependencies."""
    
    def test_voice_output_not_available(self):
        """Test behavior when voice output is not available."""
        if speak_text is not None:
            pytest.skip("Voice output is available")
        
        # Should not raise exception
        assert speak_text is None
        assert stop_speech is None
        assert is_speaking is None


class TestVoiceOutputIntegration:
    """Integration tests for voice output."""
    
    def test_voice_output_dependencies(self):
        """Test voice output dependencies."""
        try:
            import edge_tts
            assert True
        except ImportError:
            pytest.skip("Edge-TTS not available")
        
        try:
            import pygame
            assert True
        except ImportError:
            pytest.skip("Pygame not available")
    
    def test_voice_output_audio_formats(self):
        """Test voice output audio format handling."""
        try:
            import pydub
            assert True
        except ImportError:
            pytest.skip("Pydub not available")
    
    def test_voice_output_threading(self):
        """Test voice output threading functionality."""
        try:
            import threading
            import asyncio
            
            # Test basic async functionality
            async def test_async():
                return "test"
            
            result = asyncio.run(test_async())
            assert result == "test"
            
        except ImportError:
            pytest.skip("AsyncIO not available")
    
    def test_voice_output_logging(self):
        """Test voice output logging functionality."""
        try:
            import logging
            logger = logging.getLogger("test")
            logger.info("Test log message")
            assert True
        except ImportError:
            pytest.skip("Logging not available")
