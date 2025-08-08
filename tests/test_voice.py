import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import queue
import os
import pygame

# Mock external dependencies for voice_input
@pytest.fixture
def mock_speech_recognition():
    with patch('src.voice_input.sr') as MockSR:
        MockSR.Recognizer.return_value.recognize_google.return_value = "test command"
        MockSR.Microphone.return_value.__enter__.return_value = MagicMock()
        yield MockSR

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
        # Simulate playing then stopping
        MockPygame.mixer.music.get_busy.side_effect = [True, False]
        yield MockPygame

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    # Ensure no temp files are left behind by voice_output tests
    yield
    for f in os.listdir('.'):
        if f.startswith('tmp') and f.endswith('.mp3'):
            os.remove(f)

def test_voice_listener_init(mock_speech_recognition):
    from src.voice_input import VoiceListener
    q = queue.Queue()
    listener = VoiceListener(q)
    assert listener.recognizer is not None
    assert listener.command_queue == q

def test_voice_listener_start_stop(mock_speech_recognition):
    from src.voice_input import VoiceListener
    q = queue.Queue()
    listener = VoiceListener(q)
    listener.start()
    assert listener._thread.is_alive()
    listener.stop()
    listener._thread.join(timeout=1) # Give it a moment to stop
    assert not listener._thread.is_alive()

@pytest.mark.asyncio
async def test_say_function(mock_edge_tts, mock_pygame):
    from src.voice_output import say
    event = asyncio.Event()
    await say("Hello, world!", event)
    mock_edge_tts.Communicate.assert_called_once_with("Hello, world!", "en-US-JennyNeural")
    mock_edge_tts.Communicate.return_value.save.assert_awaited_once()
    mock_pygame.mixer.music.load.assert_called_once()
    mock_pygame.mixer.music.play.assert_called_once()
    mock_pygame.mixer.music.get_busy.assert_called() # Should be called at least twice (True then False)

def test_stop_speaking_function(mock_pygame):
    from src.voice_output import stop_speaking
    mock_pygame.mixer.music.get_busy.return_value = True
    stop_speaking()
    mock_pygame.mixer.music.stop.assert_called_once()