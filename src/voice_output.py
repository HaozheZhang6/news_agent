import asyncio
import edge_tts
import pygame
import tempfile
import os
import threading
import time
from .conversation_logger import conversation_logger
from .audio_logger import audio_logger
from .voice_activity_detector import vad_detector
from .config import AUDIO_RATE, CHUNK

# Lazy init flag for pygame mixer
_mixer_initialized = False

def _ensure_mixer_initialized():
    global _mixer_initialized
    if not _mixer_initialized:
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            conversation_logger.log_system_event("Pygame mixer initialized")
        except Exception as e:
            # In headless/test environments, allow mocking to handle mixer
            conversation_logger.log_error(f"Failed to initialize pygame mixer: {e}")
        _mixer_initialized = True

# Global variables for interruption handling
current_sound = None
active_speech_monitoring = False
monitoring_thread = None
speech_interrupt_callback = None


def voice_monitoring_thread():
    """Monitor for voice activity during speech playback to enable real-time interruption using sounddevice.
    Uses the same VAD logic as ASR-LLM-TTS script 14 with 40% activation rate.
    """
    import sounddevice as sd
    global active_speech_monitoring, speech_interrupt_callback

    conversation_logger.log_system_event("Voice monitoring started (using sounddevice)")

    audio_buffer = []

    # Use sounddevice's InputStream for continuous monitoring
    with sd.InputStream(
        samplerate=AUDIO_RATE,
        channels=1,
        dtype='int16',
        blocksize=CHUNK
    ) as stream:
        while active_speech_monitoring:
            try:
                data, overflowed = stream.read(CHUNK)

                if overflowed:
                    conversation_logger.log_error("Audio buffer overflow, skipping chunk")
                    continue

                # Convert numpy array to bytes for compatibility
                audio_bytes = data.tobytes()
                audio_buffer.append(audio_bytes)

                # Check for voice activity every 0.5 seconds (same as script 14)
                if len(audio_buffer) * CHUNK / AUDIO_RATE >= 0.5:
                    raw_audio = b''.join(audio_buffer)

                    # Use conservative VAD with 40% activation rate
                    if vad_detector.check_vad_activity_conservative(raw_audio, threshold_rate=0.4):
                        conversation_logger.log_interruption("Voice detected during playback")

                        # Stop current audio immediately (same as script 14)
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.stop()
                            conversation_logger.log_system_event("TTS playback stopped due to voice interruption")

                        # Call callback if provided
                        if speech_interrupt_callback:
                            speech_interrupt_callback()

                        break

                    audio_buffer = []  # Clear buffer

            except Exception as e:
                conversation_logger.log_error(f"Voice monitoring error: {e}")
                break

    conversation_logger.log_system_event("Voice monitoring stopped")

def start_voice_monitoring(interrupt_callback=None):
    """Start monitoring for voice interruptions during TTS playback."""
    global active_speech_monitoring, monitoring_thread, speech_interrupt_callback
    
    if active_speech_monitoring:
        return  # Already monitoring
    
    active_speech_monitoring = True
    speech_interrupt_callback = interrupt_callback
    
    monitoring_thread = threading.Thread(target=voice_monitoring_thread, daemon=True)
    monitoring_thread.start()

def stop_voice_monitoring():
    """Stop voice monitoring."""
    global active_speech_monitoring, monitoring_thread
    
    active_speech_monitoring = False
    
    if monitoring_thread and monitoring_thread.is_alive():
        monitoring_thread.join(timeout=1.0)

async def say(text: str, interrupt_event: asyncio.Event = None, enable_voice_interrupt: bool = True):
    """Enhanced TTS with real-time voice interruption capability.
    
    Args:
        text: Text to speak
        interrupt_event: AsyncIO event for programmatic interruption
        enable_voice_interrupt: Enable real-time voice interruption monitoring
    """
    global current_sound

    _ensure_mixer_initialized()

    # Use a temporary file for the audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        filepath = tmpfile.name

    try:
        # Check for interrupt before generation
        if interrupt_event and interrupt_event.is_set():
            return
            
        # Generate speech using edge-tts
        communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
        await communicate.save(filepath)

        # Check for interrupt after generation
        if interrupt_event and interrupt_event.is_set():
            return

        # Save response audio to output directory (handle ffmpeg issues gracefully)
        saved_audio_path = None
        try:
            saved_audio_path = audio_logger.save_response_audio(filepath)
        except Exception as e:
            conversation_logger.log_error(f"Failed to save response audio: {e}")
            # Continue without saving audio file
        
        # Log the agent response
        conversation_logger.log_agent_response(text, saved_audio_path)
        
        # Print to console for visibility
        print(f"🤖 AGENT: {text}")

        # Start voice monitoring for real-time interruption
        if enable_voice_interrupt:
            def interrupt_callback():
                # This will be called if voice is detected during playback
                if interrupt_event:
                    interrupt_event.set()
                    
            start_voice_monitoring(interrupt_callback)

        # Load and play the audio with pygame
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            
            # Wait for playback to start
            await asyncio.sleep(0.2)
            
            # Debug: Check if audio is playing
            if not pygame.mixer.music.get_busy():
                conversation_logger.log_error("Audio playback failed to start")
                return
            
            conversation_logger.log_system_event(f"TTS playback started for: {text[:50]}...")
            
            # Keep playing until finished or interrupted
            playback_time = 0
            while pygame.mixer.music.get_busy():
                if interrupt_event and interrupt_event.is_set():
                    pygame.mixer.music.stop()
                    conversation_logger.log_interruption("Programmatic interrupt")
                    break
                
                # Check for asyncio cancellation
                try:
                    await asyncio.sleep(0.1)  # 100ms check interval
                    playback_time += 0.1
                except asyncio.CancelledError:
                    pygame.mixer.music.stop()
                    conversation_logger.log_interruption("AsyncIO cancellation")
                    raise
            
            conversation_logger.log_system_event(f"TTS playback completed after {playback_time:.1f}s")
            
        except pygame.error as e:
            conversation_logger.log_error(f"Pygame audio error: {e}")
            # Try alternative playback method
            return

    except asyncio.CancelledError:
        # Ensure audio stops on cancellation
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        raise
    except Exception as e:
        conversation_logger.log_error(f"TTS error: {e}")
    finally:
        # Stop voice monitoring
        if enable_voice_interrupt:
            stop_voice_monitoring()
            
        # Ensure cleanup
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        # Ensure the temporary file is deleted
        if os.path.exists(filepath):
            os.remove(filepath)

def stop_speaking():
    """Enhanced speech stopping with voice monitoring cleanup."""
    global active_speech_monitoring
    
    try:
        # Stop voice monitoring immediately
        stop_voice_monitoring()
        
        _ensure_mixer_initialized()
        if pygame.mixer.get_init():
            # Stop all audio immediately
            pygame.mixer.music.stop()
            pygame.mixer.stop()  # Stop all sound channels too
            
            # Force fade out to ensure immediate stop
            pygame.mixer.music.fadeout(50)  # 50ms fadeout
            
            conversation_logger.log_interruption("External stop command")
    except Exception as e:
        conversation_logger.log_error(f"Error stopping speech: {e}")

def is_speaking() -> bool:
    """Check if TTS is currently playing."""
    try:
        _ensure_mixer_initialized()
        return pygame.mixer.music.get_busy()
    except:
        return False