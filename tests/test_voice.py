import pytest
from unittest.mock import MagicMock, patch, AsyncMock, mock_open
import asyncio
import queue
import os
# Do not import pygame directly; tests will patch src.voice_output.pygame
pygame = None  # noqa: F401
import tempfile
import threading
from pathlib import Path

# Mock external dependencies for voice_input (now SenseVoice)
@pytest.fixture
def mock_sensevoice():
    with patch('funasr.AutoModel') as MockAutoModel:
        mock_model = MagicMock()
        mock_model.generate.return_value = [{'text': '<|en|>test command'}]
        MockAutoModel.return_value = mock_model
        yield MockAutoModel

@pytest.fixture
def mock_pyaudio():
    with patch('pyaudio.PyAudio') as MockPyAudio:
        mock_instance = MockPyAudio.return_value
        mock_stream = MagicMock()
        mock_stream.read.return_value = b'\x00' * 1024  # Mock audio data
        mock_instance.open.return_value = mock_stream
        yield MockPyAudio

@pytest.fixture
def mock_webrtc_vad():
    with patch('webrtcvad.Vad') as MockVAD:
        mock_vad_instance = MockVAD.return_value
        mock_vad_instance.is_speech.return_value = True
        yield MockVAD

# Mock external dependencies for voice_output
@pytest.fixture
def mock_edge_tts():
    with patch('src.voice_output.edge_tts') as MockEdgeTTS:
        mock_communicate = MockEdgeTTS.Communicate.return_value
        mock_communicate.save = AsyncMock()
        yield MockEdgeTTS

@pytest.fixture
def mock_pygame():
    with patch('src.voice_output.pygame') as MockPygame:
        MockPygame.mixer.init.return_value = None
        MockPygame.mixer.music.load.return_value = None
        MockPygame.mixer.music.play.return_value = None
        MockPygame.mixer.music.stop.return_value = None
        MockPygame.mixer.get_init.return_value = True
        # Simulate playing then stopping
        MockPygame.mixer.music.get_busy.side_effect = [True, False]
        yield MockPygame

@pytest.fixture
def mock_audio_logger():
    with patch('src.voice_output.audio_logger') as MockAudioLogger:
        MockAudioLogger.save_response_audio.return_value = "/path/to/response.mp3"
        MockAudioLogger.save_segments_audio.return_value = "/path/to/input.mp3"
        yield MockAudioLogger

@pytest.fixture
def mock_conversation_logger():
    with patch('src.voice_output.conversation_logger') as MockConversationLogger:
        yield MockConversationLogger

@pytest.fixture(autouse=True)
def setup_test_environment():
    # Setup test directories and cleanup
    test_dirs = ['audio_logs', 'output', 'logs', 'logs/conversations']
    for dir_name in test_dirs:
        os.makedirs(dir_name, exist_ok=True)
    
    yield
    
    # Cleanup temp files
    for f in os.listdir('.'):
        if f.startswith('tmp') and f.endswith('.mp3'):
            try:
                os.remove(f)
            except:
                pass

def test_voice_activity_detector():
    from src.voice_activity_detector import VoiceActivityDetector
    
    with patch('webrtcvad.Vad') as MockVAD:
        mock_vad_instance = MockVAD.return_value
        mock_vad_instance.is_speech.return_value = True
        
        vad = VoiceActivityDetector()
        result = vad.check_vad_activity(b'\x00' * 1024)
        assert isinstance(result, bool)

def test_audio_logger():
    from src.audio_logger import AudioLogger
    
    with patch('wave.open') as mock_wave, \
         patch('pydub.AudioSegment') as MockAudioSegment, \
         patch('os.remove') as mock_remove:
        
        mock_segment = MockAudioSegment.from_wav.return_value
        logger = AudioLogger()
        
        # Test saving input audio
        result = logger.save_input_audio(b'\x00' * 1024)
        assert result.endswith('.mp3')
        mock_wave.assert_called()
        mock_segment.export.assert_called()

def test_conversation_logger():
    from src.conversation_logger import ConversationLogger
    
    with patch('builtins.open', mock_open()) as mock_file:
        logger = ConversationLogger()
        
        # Test logging user input
        logger.log_user_input("test input", "/path/to/audio.mp3")
        mock_file.assert_called()
        
        # Test logging agent response
        logger.log_agent_response("test response", "/path/to/response.mp3")
        mock_file.assert_called()
        
        # Test system events
        logger.log_system_event("test event")
        mock_file.assert_called()

@pytest.mark.asyncio
async def test_enhanced_say_function(mock_edge_tts, mock_pygame, mock_audio_logger, mock_conversation_logger):
    from src.voice_output import say
    
    with patch('src.voice_output.start_voice_monitoring') as mock_start_monitoring, \
         patch('src.voice_output.stop_voice_monitoring') as mock_stop_monitoring:
        
        event = asyncio.Event()
        await say("Hello, world!", event, enable_voice_interrupt=True)
        
        # Test TTS generation
        mock_edge_tts.Communicate.assert_called_once_with("Hello, world!", "en-US-JennyNeural")
        mock_edge_tts.Communicate.return_value.save.assert_awaited_once()
        
        # Test audio playback
        mock_pygame.mixer.music.load.assert_called_once()
        mock_pygame.mixer.music.play.assert_called_once()
        
        # Test voice monitoring
        mock_start_monitoring.assert_called_once()
        mock_stop_monitoring.assert_called_once()
        
        # Test logging
        mock_audio_logger.save_response_audio.assert_called_once()
        mock_conversation_logger.log_agent_response.assert_called_once()

@pytest.mark.asyncio 
async def test_say_with_interrupt(mock_edge_tts, mock_pygame, mock_audio_logger, mock_conversation_logger):
    from src.voice_output import say
    
    with patch('src.voice_output.start_voice_monitoring'), \
         patch('src.voice_output.stop_voice_monitoring'):
        
        event = asyncio.Event()
        event.set()  # Pre-set interrupt event
        
        await say("This should be interrupted", event)
        
        # Should not generate TTS if interrupted early
        mock_edge_tts.Communicate.assert_not_called()

def test_enhanced_stop_speaking_function(mock_pygame, mock_conversation_logger):
    from src.voice_output import stop_speaking
    
    with patch('src.voice_output.stop_voice_monitoring') as mock_stop_monitoring:
        mock_pygame.mixer.music.get_busy.return_value = True
        
        stop_speaking()
        
        mock_pygame.mixer.music.stop.assert_called_once()
        mock_stop_monitoring.assert_called_once()
        mock_conversation_logger.log_interruption.assert_called_once()

def test_voice_monitoring_thread(mock_pyaudio, mock_webrtc_vad, mock_conversation_logger):
    from src.voice_output import voice_monitoring_thread, active_speech_monitoring
    
    with patch('src.voice_output.active_speech_monitoring', True), \
         patch('src.voice_output.vad_detector') as mock_vad, \
         patch('pygame.mixer.music.get_busy', return_value=True) as mock_busy, \
         patch('pygame.mixer.music.stop') as mock_stop:
        
        # Mock VAD to detect speech
        mock_vad.check_vad_activity.return_value = True
        
        # Run monitoring in a separate thread briefly
        thread = threading.Thread(target=voice_monitoring_thread, daemon=True)
        thread.start()
        thread.join(timeout=0.5)
        
        # Should have checked for voice activity
        mock_vad.check_vad_activity.assert_called()

def test_command_classification():
    from src.voice_listener_process import classify_intent
    from src.ipc import CommandType
    
    # Test stop commands
    cmd = classify_intent("stop")
    assert cmd.type == CommandType.STOP
    
    # Test deep dive commands
    cmd = classify_intent("tell me more")
    assert cmd.type == CommandType.DEEP_DIVE
    
    # Test navigation commands
    cmd = classify_intent("skip this")
    assert cmd.type == CommandType.SKIP
    
    # Test volume commands
    cmd = classify_intent("speak louder")
    assert cmd.type == CommandType.VOLUME_UP
    
    # Test content requests
    cmd = classify_intent("latest news")
    assert cmd.type == CommandType.NEWS_REQUEST
    
    cmd = classify_intent("stock prices")
    assert cmd.type == CommandType.STOCK_REQUEST
    
    cmd = classify_intent("weather forecast")
    assert cmd.type == CommandType.WEATHER_REQUEST

def test_sensevoice_integration(mock_sensevoice, mock_pyaudio, mock_webrtc_vad, mock_audio_logger):
    from src.voice_listener_process import process_audio_segments
    import multiprocessing as mp
    
    # Mock the global segments
    with patch('src.voice_listener_process.segments_to_save', [(b'\x00' * 1024, 123456.0)]):
        command_queue = mp.Queue()
        interrupt_event = mp.Event()
        shared_state = mp.Manager().dict()
        
        # Mock the model loading
        with patch.object(process_audio_segments, 'sensevoice_model', mock_sensevoice.return_value):
            process_audio_segments(command_queue, interrupt_event, shared_state)
            
            # Should save audio and run recognition
            mock_audio_logger.save_segments_audio.assert_called_once()
            mock_sensevoice.return_value.generate.assert_called_once()
            
            # Should put command in queue
            assert not command_queue.empty()

@pytest.mark.asyncio
async def test_is_speaking_function(mock_pygame):
    from src.voice_output import is_speaking
    
    mock_pygame.mixer.music.get_busy.return_value = True
    assert is_speaking() == True
    
    mock_pygame.mixer.music.get_busy.return_value = False
    assert is_speaking() == False