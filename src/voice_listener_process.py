"""Voice listener thread for continuous speech recognition with SenseVoice."""
import threading
import time
try:
    import pyaudio
except Exception:  # pragma: no cover - optional dependency for CI/test envs
    pyaudio = None  # type: ignore
import os
from .config import (
    AUDIO_RATE, AUDIO_CHANNELS, CHUNK, NO_SPEECH_THRESHOLD,
    SENSEVOICE_MODEL_PATH
)
from .voice_activity_detector import vad_detector
from .audio_logger import audio_logger
from .conversation_logger import conversation_logger

# Global variables for audio processing
last_active_time = time.time()
recording_active = True
segments_to_save = []
last_vad_end_time = 0

def classify_intent(text: str):
    """Enhanced intent classification for user interactions."""
    from .ipc import Command, CommandType, CommandPriority
    
    text_lower = text.lower()
    
    # Immediate interrupt commands - highest priority
    if any(word in text_lower for word in ["stop", "halt", "pause", "quiet", "silence", "shut up", "cancel"]):
        return Command(CommandType.STOP, original_text=text)
    
    if any(word in text_lower for word in ["continue", "resume", "go on", "proceed"]):
        return Command(CommandType.CONTINUE, original_text=text)
    
    # Deep dive commands
    if any(phrase in text_lower for phrase in [
        "tell me more", "dive deeper", "explain", "elaborate", "expand",
        "more details", "go deeper", "continue with", "tell me about"
    ]):
        return Command(CommandType.DEEP_DIVE, original_text=text)
    
    # Navigation commands    
    if any(word in text_lower for word in ["skip", "next", "move on", "skip this"]):
        return Command(CommandType.SKIP, original_text=text)
    
    if any(phrase in text_lower for phrase in ["go back", "previous", "repeat", "say again"]):
        return Command(CommandType.REPEAT, original_text=text)
    
    # Volume/speed control
    if any(phrase in text_lower for phrase in ["speak louder", "volume up", "louder"]):
        return Command(CommandType.VOLUME_UP, original_text=text)
        
    if any(phrase in text_lower for phrase in ["speak quieter", "volume down", "quieter", "lower"]):
        return Command(CommandType.VOLUME_DOWN, original_text=text)
        
    if any(phrase in text_lower for phrase in ["speak faster", "speed up", "faster"]):
        return Command(CommandType.SPEED_UP, original_text=text)
        
    if any(phrase in text_lower for phrase in ["speak slower", "slow down", "slower"]):
        return Command(CommandType.SPEED_DOWN, original_text=text)
    
    # Content requests with enhanced keywords (order matters - check weather first!)
    if any(word in text_lower for word in [
        "weather", "temperature", "forecast", "climate"
    ]):
        return Command(CommandType.WEATHER_REQUEST, data=text, original_text=text)
        
    if any(word in text_lower for word in [
        "stock", "price", "ticker", "market", "trading", "shares", "investment"
    ]):
        return Command(CommandType.STOCK_REQUEST, data=text, original_text=text)
    
    if any(word in text_lower for word in [
        "news", "headlines", "latest", "breaking", "current events"
    ]):
        return Command(CommandType.NEWS_REQUEST, data=text, original_text=text)
    
    # Help and settings
    if any(phrase in text_lower for phrase in ["help", "what can you do", "commands", "options"]):
        return Command(CommandType.HELP)
        
    # Default to news request for any unclassified input
    return Command(CommandType.NEWS_REQUEST, data=text)

def audio_recorder_worker(command_queue, interrupt_event, ipc_manager):
    """Audio recording worker with VAD-based speech detection."""
    global recording_active, last_active_time, segments_to_save, last_vad_end_time
    
    conversation_logger.log_system_event("Audio recording started with SenseVoice")
    if pyaudio is None:
        conversation_logger.log_error("PyAudio not available; skipping live recording in tests")
        return

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=AUDIO_CHANNELS,
        rate=AUDIO_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    
    audio_buffer = []
    
    while recording_active:
        try:
            data = stream.read(CHUNK)
            audio_buffer.append(data)
            
            # Check VAD every 0.5 seconds
            if len(audio_buffer) * CHUNK / AUDIO_RATE >= 0.5:
                raw_audio = b''.join(audio_buffer)
                vad_result = vad_detector.check_vad_activity(raw_audio)
                
                if vad_result:
                    conversation_logger.log_speech_detection(True)
                    last_active_time = time.time()
                    segments_to_save.append((raw_audio, time.time()))
                else:
                    conversation_logger.log_speech_detection(False)
                
                audio_buffer = []  # Clear buffer
            
            # Check if we should process saved segments
            if time.time() - last_active_time > NO_SPEECH_THRESHOLD:
                if segments_to_save and segments_to_save[-1][1] > last_vad_end_time:
                    process_audio_segments(command_queue, interrupt_event, ipc_manager)
                    last_active_time = time.time()
                    
        except Exception as e:
            conversation_logger.log_error(f"Audio recording error: {e}")
            time.sleep(0.1)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    conversation_logger.log_system_event("Audio recording stopped")

def process_audio_segments(command_queue, interrupt_event, ipc_manager):
    """Process recorded audio segments with SenseVoice."""
    global segments_to_save, last_vad_end_time
    
    if not segments_to_save:
        return
    
    try:
        # Save audio segments to file
        audio_file = audio_logger.save_segments_audio(segments_to_save, "input")
        
        # Initialize SenseVoice model (lazy loading)
        if not hasattr(process_audio_segments, 'sensevoice_model'):
            try:
                # TODO: Remove this once we have a proper model
                from funasr import AutoModel
                process_audio_segments.sensevoice_model = AutoModel(
                    model=SENSEVOICE_MODEL_PATH,
                    trust_remote_code=True
                )
                conversation_logger.log_system_event("SenseVoice model loaded")
            except Exception as e:
                conversation_logger.log_error(f"Failed to load SenseVoice model: {e}")
                # Fallback to dummy recognition
                segments_to_save.clear()
                return
        
        # Run SenseVoice recognition
        res = process_audio_segments.sensevoice_model.generate(
            input=audio_file,
            cache={},
            language="auto",
            use_itn=False,
        )
        
        if res and len(res) > 0 and 'text' in res[0]:
            # Extract text (remove language tags)
            text = res[0]['text'].split(">")[-1].strip()
            
            if text:  # Only process non-empty text
                conversation_logger.log_user_input(text, audio_file)
                
                # Classify and send command
                command = classify_intent(text)
                command_queue.put(command)
                
                # Set interrupt for immediate commands
                if command.type.value in ["stop", "deep_dive"]:
                    interrupt_event.set()
                    ipc_manager.set_state('interrupt_requested', True)
                    conversation_logger.log_interruption(f"Command: {text}")
        
        # Update last processed time
        last_vad_end_time = segments_to_save[-1][1] if segments_to_save else 0
        segments_to_save.clear()
        
    except Exception as e:
        conversation_logger.log_error(f"SenseVoice processing error: {e}")
        segments_to_save.clear()

def fallback_voice_listener_worker(command_queue, interrupt_event, ipc_manager):
    """Fallback voice listener using speech_recognition library."""
    try:
        import speech_recognition as sr
        conversation_logger.log_system_event("Using fallback speech recognition")
        
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        # Adjust for ambient noise once
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
        
        while True:
            try:
                # Listen for speech
                with microphone as source:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Fast recognition
                try:
                    text = recognizer.recognize_google(audio)
                    conversation_logger.log_user_input(text)
                    
                    # Print to console for visibility
                    print(f"👤 USER: {text}")
                    
                    # Classify and send command immediately  
                    command = classify_intent(text)
                    command_queue.put(command)
                    
                    # Set interrupt for immediate commands
                    if command.type.value in ["stop", "deep_dive"]:
                        interrupt_event.set()
                        ipc_manager.set_state('interrupt_requested', True)
                        
                except sr.UnknownValueError:
                    pass  # Ignore unrecognized speech
                    
            except sr.WaitTimeoutError:
                pass  # Continue listening
            except Exception as e:
                conversation_logger.log_error(f"Fallback listener error: {e}")
                time.sleep(0.1)
                
    except ImportError:
        conversation_logger.log_error("Neither SenseVoice nor speech_recognition available")
        return

def voice_listener_worker(command_queue, interrupt_event, ipc_manager):
    """Main worker function for voice listener thread."""
    global recording_active
    
    # Check if SenseVoice model exists
    if not os.path.exists(SENSEVOICE_MODEL_PATH):
        conversation_logger.log_error(f"SenseVoice model not found at: {SENSEVOICE_MODEL_PATH}")
        conversation_logger.log_system_event("Falling back to basic voice listener")
        # Fall back to original speech recognition
        fallback_voice_listener_worker(command_queue, interrupt_event, ipc_manager)
        return
    
    recording_active = True
    
    try:
        audio_recorder_worker(command_queue, interrupt_event, ipc_manager)
    except KeyboardInterrupt:
        conversation_logger.log_system_event("Voice listener interrupted")
    finally:
        recording_active = False

def start_listener_thread(ipc_manager):
    """Start the voice listener in a separate thread."""
    thread = threading.Thread(
        target=voice_listener_worker,
        args=(ipc_manager.command_queue, ipc_manager.interrupt_event, ipc_manager),
        daemon=True
    )
    thread.start()
    return thread