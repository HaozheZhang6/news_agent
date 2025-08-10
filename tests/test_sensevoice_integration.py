"""Test SenseVoice integration and enhanced voice processing functionality."""
import pytest
import asyncio
import multiprocessing as mp
import threading
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock, mock_open
from pathlib import Path


@pytest.fixture
def mock_sensevoice():
    """Mock SenseVoice (FunASR) model."""
    with patch('funasr.AutoModel') as MockAutoModel:
        mock_model = MagicMock()
        mock_model.generate.return_value = [{'text': '<|en|>test command'}]
        MockAutoModel.return_value = mock_model
        yield MockAutoModel


@pytest.fixture
def mock_pyaudio():
    """Mock PyAudio for audio recording."""
    with patch('pyaudio.PyAudio') as MockPyAudio:
        mock_instance = MockPyAudio.return_value
        mock_stream = MagicMock()
        mock_stream.read.return_value = b'\x00' * 1024  # Mock audio data
        mock_instance.open.return_value = mock_stream
        yield MockPyAudio


@pytest.fixture
def mock_webrtc_vad():
    """Mock WebRTC VAD."""
    with patch('webrtcvad.Vad') as MockVAD:
        mock_vad_instance = MockVAD.return_value
        mock_vad_instance.is_speech.return_value = True
        yield MockVAD


@pytest.fixture
def mock_pygame():
    """Mock pygame mixer."""
    with patch('pygame.mixer') as MockMixer:
        MockMixer.init.return_value = None
        MockMixer.music.load.return_value = None
        MockMixer.music.play.return_value = None
        MockMixer.music.stop.return_value = None
        MockMixer.music.get_busy.side_effect = [True, False]
        MockMixer.get_init.return_value = True
        yield MockMixer


@pytest.fixture
def mock_edge_tts():
    """Mock Edge-TTS."""
    with patch('edge_tts.Communicate') as MockCommunicate:
        mock_communicate_instance = MockCommunicate.return_value
        mock_communicate_instance.save = AsyncMock()
        yield MockCommunicate


@pytest.fixture
def test_directories():
    """Create test directories."""
    import os
    test_dirs = ['audio_logs', 'output', 'logs', 'logs/conversations']
    for dir_name in test_dirs:
        os.makedirs(dir_name, exist_ok=True)
    yield
    # Cleanup handled by other fixtures


class TestSenseVoiceIntegration:
    """Test SenseVoice ASR integration."""
    
    def test_sensevoice_model_loading(self, mock_sensevoice):
        """Test SenseVoice model loading and initialization."""
        from src.voice_listener_process import process_audio_segments
        
        # Mock segments and IPC
        with patch('src.voice_listener_process.segments_to_save', [(b'\x00' * 1024, 123456.0)]), \
             patch('src.audio_logger.audio_logger.save_segments_audio') as mock_save:
            
            command_queue = mp.Queue()
            interrupt_event = mp.Event()
            shared_state = mp.Manager().dict()
            
            mock_save.return_value = "/test/audio.mp3"
            
            # First call should load model
            process_audio_segments(command_queue, interrupt_event, shared_state)
            
            # Should have created model instance
            mock_sensevoice.assert_called_once()
            
            # Should have generated recognition
            mock_sensevoice.return_value.generate.assert_called_once()
    
    def test_sensevoice_recognition_pipeline(self, mock_sensevoice):
        """Test complete SenseVoice recognition pipeline."""
        from src.voice_listener_process import process_audio_segments
        
        # Mock recognition result
        mock_sensevoice.return_value.generate.return_value = [
            {'text': '<|en|>tell me more about the news'}
        ]
        
        with patch('src.voice_listener_process.segments_to_save', [(b'\x00' * 1024, 123456.0)]), \
             patch('src.audio_logger.audio_logger.save_segments_audio') as mock_save, \
             patch('src.conversation_logger.conversation_logger.log_user_input') as mock_log:
            
            command_queue = mp.Queue()
            interrupt_event = mp.Event()
            shared_state = mp.Manager().dict()
            
            mock_save.return_value = "/test/input.mp3"
            
            # Mock model as already loaded
            with patch.object(process_audio_segments, 'sensevoice_model', mock_sensevoice.return_value):
                process_audio_segments(command_queue, interrupt_event, shared_state)
            
            # Should have logged user input
            mock_log.assert_called_once_with("tell me more about the news", "/test/input.mp3")
            
            # Should have queued command
            assert not command_queue.empty()
            command = command_queue.get()
            from src.ipc import CommandType
            assert command.type == CommandType.DEEP_DIVE
    
    def test_sensevoice_multilingual_support(self, mock_sensevoice):
        """Test SenseVoice multilingual recognition."""
        from src.voice_listener_process import process_audio_segments
        
        # Test different language outputs
        test_cases = [
            ('<|zh|>停止播放', '停止播放'),
            ('<|en|>stop talking', 'stop talking'),
            ('<|ja|>もっと教えて', 'もっと教えて'),
        ]
        
        for sensevoice_output, expected_text in test_cases:
            mock_sensevoice.return_value.generate.return_value = [{'text': sensevoice_output}]
            
            with patch('src.voice_listener_process.segments_to_save', [(b'\x00' * 1024, 123456.0)]), \
                 patch('src.audio_logger.audio_logger.save_segments_audio') as mock_save, \
                 patch('src.conversation_logger.conversation_logger.log_user_input') as mock_log:
                
                command_queue = mp.Queue()
                interrupt_event = mp.Event()
                shared_state = mp.Manager().dict()
                
                mock_save.return_value = "/test/multilingual.mp3"
                
                # Mock model as already loaded
                with patch.object(process_audio_segments, 'sensevoice_model', mock_sensevoice.return_value):
                    process_audio_segments(command_queue, interrupt_event, shared_state)
                
                # Should extract text correctly regardless of language
                mock_log.assert_called_with(expected_text, "/test/multilingual.mp3")
    
    def test_sensevoice_error_handling(self, mock_sensevoice):
        """Test SenseVoice error handling and fallback."""
        from src.voice_listener_process import process_audio_segments
        
        # Mock SenseVoice to raise exception
        mock_sensevoice.return_value.generate.side_effect = Exception("Recognition failed")
        
        with patch('src.voice_listener_process.segments_to_save', [(b'\x00' * 1024, 123456.0)]), \
             patch('src.audio_logger.audio_logger.save_segments_audio') as mock_save, \
             patch('src.conversation_logger.conversation_logger.log_error') as mock_log_error:
            
            command_queue = mp.Queue()
            interrupt_event = mp.Event()
            shared_state = mp.Manager().dict()
            
            mock_save.return_value = "/test/error.mp3"
            
            # Mock model as already loaded
            with patch.object(process_audio_segments, 'sensevoice_model', mock_sensevoice.return_value):
                process_audio_segments(command_queue, interrupt_event, shared_state)
            
            # Should have logged error
            mock_log_error.assert_called_once()
            
            # Queue should be empty (no commands processed)
            assert command_queue.empty()


class TestVoiceActivityDetection:
    """Test Voice Activity Detection integration."""
    
    def test_vad_initialization(self, mock_webrtc_vad):
        """Test VAD initialization with different modes."""
        from src.voice_activity_detector import VoiceActivityDetector
        
        # Test default mode
        vad = VoiceActivityDetector()
        mock_webrtc_vad.return_value.set_mode.assert_called_with(3)
        
        # Test custom mode
        vad = VoiceActivityDetector(mode=1)
        mock_webrtc_vad.return_value.set_mode.assert_called_with(1)
    
    def test_vad_speech_detection(self, mock_webrtc_vad):
        """Test VAD speech detection logic."""
        from src.voice_activity_detector import VoiceActivityDetector
        
        vad = VoiceActivityDetector()
        
        # Mock all frames as speech
        mock_webrtc_vad.return_value.is_speech.return_value = True
        
        result = vad.check_vad_activity(b'\x00' * 1600, threshold_rate=0.4)  # 100ms of audio
        assert result == True
        
        # Mock no speech
        mock_webrtc_vad.return_value.is_speech.return_value = False
        
        result = vad.check_vad_activity(b'\x00' * 1600, threshold_rate=0.4)
        assert result == False
    
    def test_vad_threshold_behavior(self, mock_webrtc_vad):
        """Test VAD threshold behavior with mixed speech/silence."""
        from src.voice_activity_detector import VoiceActivityDetector
        
        vad = VoiceActivityDetector()
        
        # Mock 30% of frames as speech (below 40% threshold)
        call_count = 0
        def mock_is_speech(*args):
            nonlocal call_count
            call_count += 1
            return call_count % 10 < 3  # 30% true
        
        mock_webrtc_vad.return_value.is_speech.side_effect = mock_is_speech
        
        result = vad.check_vad_activity(b'\x00' * 1600, threshold_rate=0.4)
        assert result == False  # Below threshold
        
        # Reset and test 50% speech (above threshold)
        call_count = 0
        def mock_is_speech_high(*args):
            nonlocal call_count
            call_count += 1
            return call_count % 10 < 5  # 50% true
        
        mock_webrtc_vad.return_value.is_speech.side_effect = mock_is_speech_high
        
        result = vad.check_vad_activity(b'\x00' * 1600, threshold_rate=0.4)
        assert result == True  # Above threshold


class TestAudioLogging:
    """Test audio logging functionality."""
    
    def test_input_audio_logging(self):
        """Test logging of input audio as MP3."""
        from src.audio_logger import AudioLogger
        
        with patch('wave.open') as mock_wave, \
             patch('pydub.AudioSegment') as MockAudioSegment, \
             patch('os.remove') as mock_remove:
            
            mock_segment = MockAudioSegment.from_wav.return_value
            logger = AudioLogger()
            
            result = logger.save_input_audio(b'\x00' * 1024, "test_input")
            
            # Should save as WAV first, convert to MP3, then remove WAV
            mock_wave.assert_called_once()
            MockAudioSegment.from_wav.assert_called_once()
            mock_segment.export.assert_called_once()
            mock_remove.assert_called_once()
            
            assert "test_input" in result
            assert result.endswith('.mp3')
    
    def test_segments_audio_logging(self):
        """Test logging of audio segments from VAD processing."""
        from src.audio_logger import AudioLogger
        
        segments = [
            (b'\x00' * 512, 123456.0),
            (b'\x00' * 256, 123456.5)
        ]
        
        with patch('wave.open') as mock_wave, \
             patch('pydub.AudioSegment') as MockAudioSegment, \
             patch('os.remove') as mock_remove:
            
            mock_segment = MockAudioSegment.from_wav.return_value
            logger = AudioLogger()
            
            result = logger.save_segments_audio(segments, "vad_input")
            
            # Should combine segments and save
            mock_wave.assert_called_once()
            
            # Check that segments were combined
            write_calls = mock_wave.return_value.__enter__.return_value.writeframes.call_args_list
            assert len(write_calls) == 1
            written_data = write_calls[0][0][0]
            assert len(written_data) == 768  # 512 + 256
            
            assert result.endswith('.mp3')
    
    def test_response_audio_logging(self):
        """Test logging of TTS response audio."""
        from src.audio_logger import AudioLogger
        
        with patch('os.path.exists', return_value=True), \
             patch('pydub.AudioSegment') as MockAudioSegment:
            
            mock_segment = MockAudioSegment.from_file.return_value
            logger = AudioLogger()
            
            result = logger.save_response_audio("/temp/tts_output.mp3")
            
            MockAudioSegment.from_file.assert_called_once_with("/temp/tts_output.mp3")
            mock_segment.export.assert_called_once()
            
            assert "response" in result
            assert result.endswith('.mp3')


class TestConversationLogging:
    """Test conversation logging functionality."""
    
    def test_conversation_file_creation(self):
        """Test daily conversation file creation."""
        from src.conversation_logger import ConversationLogger
        
        with patch('builtins.open', mock_open()) as mock_file:
            logger = ConversationLogger()
            
            # Test file creation
            conv_file = logger.get_conversation_file()
            
            assert str(conv_file).endswith('.txt')
            assert 'conversation_' in str(conv_file)
    
    def test_user_input_logging(self):
        """Test logging of user voice input."""
        from src.conversation_logger import ConversationLogger
        
        with patch('builtins.open', mock_open()) as mock_file:
            logger = ConversationLogger()
            
            logger.log_user_input("tell me the news", "/audio/input_123.mp3")
            
            # Should write to conversation file
            mock_file.assert_called()
            written_content = mock_file.return_value.__enter__.return_value.write.call_args_list
            
            # Check content includes timestamp, USER label, text, and audio file
            written_text = ''.join([call[0][0] for call in written_content])
            assert 'USER:' in written_text
            assert '"tell me the news"' in written_text
            assert 'Audio: /audio/input_123.mp3' in written_text
    
    def test_agent_response_logging(self):
        """Test logging of agent responses."""
        from src.conversation_logger import ConversationLogger
        
        with patch('builtins.open', mock_open()) as mock_file:
            logger = ConversationLogger()
            
            logger.log_agent_response("Here are today's headlines", "/audio/response_123.mp3")
            
            written_content = mock_file.return_value.__enter__.return_value.write.call_args_list
            written_text = ''.join([call[0][0] for call in written_content])
            
            assert 'AGENT:' in written_text
            assert '"Here are today\'s headlines"' in written_text
            assert 'Audio: /audio/response_123.mp3' in written_text
    
    def test_system_event_logging(self):
        """Test logging of system events like interruptions."""
        from src.conversation_logger import ConversationLogger
        
        with patch('builtins.open', mock_open()) as mock_file:
            logger = ConversationLogger()
            
            logger.log_interruption("Voice detected during playback")
            
            written_content = mock_file.return_value.__enter__.return_value.write.call_args_list
            written_text = ''.join([call[0][0] for call in written_content])
            
            assert 'SYSTEM:' in written_text
            assert 'Audio playback interrupted: Voice detected during playback' in written_text


class TestRealTimeInterruption:
    """Test real-time voice interruption during TTS playback."""
    
    @pytest.mark.asyncio
    async def test_voice_monitoring_interruption(self, mock_pygame, mock_pyaudio, mock_webrtc_vad):
        """Test voice monitoring detecting speech and interrupting TTS."""
        from src.voice_output import voice_monitoring_thread
        
        with patch('src.voice_output.vad_detector') as mock_vad, \
             patch('src.voice_output.active_speech_monitoring', True), \
             patch('src.voice_output.conversation_logger') as mock_logger:
            
            # Mock VAD to detect speech
            mock_vad.check_vad_activity.return_value = True
            mock_pygame.music.get_busy.return_value = True
            
            # Mock pyaudio stream
            mock_stream = MagicMock()
            mock_stream.read.return_value = b'\x00' * 1024
            mock_pyaudio.return_value.open.return_value = mock_stream
            
            # Run monitoring briefly
            monitor_thread = threading.Thread(target=voice_monitoring_thread, daemon=True)
            monitor_thread.start()
            
            # Give time for voice detection
            await asyncio.sleep(0.3)
            
            # Stop monitoring
            with patch('src.voice_output.active_speech_monitoring', False):
                monitor_thread.join(timeout=1.0)
            
            # Should have detected voice activity
            mock_vad.check_vad_activity.assert_called()
            
            # Should have stopped music due to voice detection
            mock_pygame.music.stop.assert_called()
            
            # Should have logged interruption
            mock_logger.log_interruption.assert_called()
    
    @pytest.mark.asyncio
    async def test_enhanced_say_with_interruption(self, mock_edge_tts, mock_pygame):
        """Test enhanced say function with voice interruption capability."""
        from src.voice_output import say
        
        with patch('src.voice_output.start_voice_monitoring') as mock_start, \
             patch('src.voice_output.stop_voice_monitoring') as mock_stop, \
             patch('src.voice_output.audio_logger') as mock_audio_logger, \
             patch('src.voice_output.conversation_logger') as mock_conv_logger:
            
            mock_audio_logger.save_response_audio.return_value = "/output/response.mp3"
            
            interrupt_event = asyncio.Event()
            
            await say("Test message", interrupt_event, enable_voice_interrupt=True)
            
            # Should have started and stopped voice monitoring
            mock_start.assert_called_once()
            mock_stop.assert_called_once()
            
            # Should have logged response
            mock_conv_logger.log_agent_response.assert_called_once()
            mock_audio_logger.save_response_audio.assert_called_once()
    
    def test_stop_speaking_with_monitoring_cleanup(self, mock_pygame):
        """Test enhanced stop_speaking function cleans up voice monitoring."""
        from src.voice_output import stop_speaking
        
        with patch('src.voice_output.stop_voice_monitoring') as mock_stop, \
             patch('src.voice_output.conversation_logger') as mock_logger:
            
            stop_speaking()
            
            # Should stop voice monitoring
            mock_stop.assert_called_once()
            
            # Should stop pygame
            mock_pygame.music.stop.assert_called_once()
            mock_pygame.stop.assert_called_once()
            
            # Should log interruption
            mock_logger.log_interruption.assert_called_once()


class TestEnhancedCommandClassification:
    """Test enhanced command classification with new command types."""
    
    def test_comprehensive_command_classification(self):
        """Test all enhanced command classifications."""
        from src.voice_listener_process import classify_intent
        from src.ipc import CommandType
        
        test_cases = [
            # Stop commands
            ("stop", CommandType.STOP),
            ("halt", CommandType.STOP),
            ("quiet", CommandType.STOP),
            ("silence", CommandType.STOP),
            ("shut up", CommandType.STOP),
            
            # Continue commands
            ("continue", CommandType.CONTINUE),
            ("resume", CommandType.CONTINUE),
            ("go on", CommandType.CONTINUE),
            ("proceed", CommandType.CONTINUE),
            
            # Deep dive commands
            ("tell me more", CommandType.DEEP_DIVE),
            ("dive deeper", CommandType.DEEP_DIVE),
            ("explain", CommandType.DEEP_DIVE),
            ("elaborate", CommandType.DEEP_DIVE),
            ("expand", CommandType.DEEP_DIVE),
            ("more details", CommandType.DEEP_DIVE),
            
            # Navigation commands
            ("skip", CommandType.SKIP),
            ("next", CommandType.SKIP),
            ("move on", CommandType.SKIP),
            ("skip this", CommandType.SKIP),
            ("go back", CommandType.REPEAT),
            ("previous", CommandType.REPEAT),
            ("repeat", CommandType.REPEAT),
            ("say again", CommandType.REPEAT),
            
            # Volume/speed control
            ("speak louder", CommandType.VOLUME_UP),
            ("volume up", CommandType.VOLUME_UP),
            ("louder", CommandType.VOLUME_UP),
            ("speak quieter", CommandType.VOLUME_DOWN),
            ("volume down", CommandType.VOLUME_DOWN),
            ("quieter", CommandType.VOLUME_DOWN),
            ("speak faster", CommandType.SPEED_UP),
            ("speed up", CommandType.SPEED_UP),
            ("faster", CommandType.SPEED_UP),
            ("speak slower", CommandType.SPEED_DOWN),
            ("slow down", CommandType.SPEED_DOWN),
            ("slower", CommandType.SPEED_DOWN),
            
            # Content requests
            ("news", CommandType.NEWS_REQUEST),
            ("headlines", CommandType.NEWS_REQUEST),
            ("latest", CommandType.NEWS_REQUEST),
            ("breaking", CommandType.NEWS_REQUEST),
            ("current events", CommandType.NEWS_REQUEST),
            ("stock", CommandType.STOCK_REQUEST),
            ("price", CommandType.STOCK_REQUEST),
            ("ticker", CommandType.STOCK_REQUEST),
            ("market", CommandType.STOCK_REQUEST),
            ("trading", CommandType.STOCK_REQUEST),
            ("shares", CommandType.STOCK_REQUEST),
            ("investment", CommandType.STOCK_REQUEST),
            ("weather", CommandType.WEATHER_REQUEST),
            ("temperature", CommandType.WEATHER_REQUEST),
            ("forecast", CommandType.WEATHER_REQUEST),
            ("climate", CommandType.WEATHER_REQUEST),
            
            # Help and settings
            ("help", CommandType.HELP),
            ("what can you do", CommandType.HELP),
            ("commands", CommandType.HELP),
            ("options", CommandType.HELP),
            ("settings", CommandType.SETTINGS),
            ("configure", CommandType.SETTINGS),
            ("preferences", CommandType.SETTINGS),
        ]
        
        for text, expected_type in test_cases:
            command = classify_intent(text)
            assert command.type == expected_type, f"Failed for text: '{text}', expected {expected_type}, got {command.type}"
    
    def test_command_data_preservation(self):
        """Test that command data is properly preserved for content requests."""
        from src.voice_listener_process import classify_intent
        from src.ipc import CommandType
        
        content_requests = [
            "tell me about Apple stock",
            "latest news on technology",
            "weather forecast for tomorrow"
        ]
        
        for text in content_requests:
            command = classify_intent(text)
            
            # Content requests should preserve original text
            if command.type in [CommandType.NEWS_REQUEST, CommandType.STOCK_REQUEST, CommandType.WEATHER_REQUEST]:
                assert command.data == text
    
    def test_interrupt_command_identification(self):
        """Test identification of commands that should trigger immediate interrupts."""
        from src.voice_listener_process import classify_intent
        from src.ipc import CommandType
        
        # Commands that should trigger interrupts
        interrupt_commands = ["stop", "halt", "tell me more", "dive deeper"]
        
        # Commands that should not trigger interrupts
        non_interrupt_commands = ["skip", "louder", "news", "weather"]
        
        interrupt_types = [CommandType.STOP, CommandType.DEEP_DIVE]
        
        for text in interrupt_commands:
            command = classify_intent(text)
            assert command.type in interrupt_types, f"Command '{text}' should trigger interrupt"
        
        for text in non_interrupt_commands:
            command = classify_intent(text)
            assert command.type not in interrupt_types, f"Command '{text}' should not trigger interrupt"


if __name__ == '__main__':
    pytest.main([__file__])