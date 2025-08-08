"""Voice listener process for continuous speech recognition."""
import multiprocessing as mp
import time

def classify_intent(text: str):
    """Fast intent classification for immediate commands."""
    from .ipc import Command, CommandType
    
    text_lower = text.lower()
    
    # Immediate interrupt commands
    if any(word in text_lower for word in ["stop", "pause", "quiet"]):
        return Command(CommandType.STOP)
    
    if any(phrase in text_lower for phrase in ["tell me more", "dive deeper", "explain"]):
        return Command(CommandType.DEEP_DIVE)
        
    if "skip" in text_lower:
        return Command(CommandType.SKIP)
        
    # Content requests  
    if any(word in text_lower for word in ["news", "headlines", "latest"]):
        return Command(CommandType.NEWS_REQUEST, data=text)
        
    if any(word in text_lower for word in ["stock", "price", "ticker"]):
        return Command(CommandType.STOCK_REQUEST, data=text)
        
    # Default to news request
    return Command(CommandType.NEWS_REQUEST, data=text)

def voice_listener_worker(command_queue, interrupt_event, shared_state):
    """Worker function for voice listener process."""
    import speech_recognition as sr
    
    print("Voice listener started...")
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient noise once
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
    
    while True:
        try:
            # Listen for speech (non-blocking)
            with microphone as source:
                # Short timeout for responsiveness
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
            
            # Fast recognition
            try:
                text = recognizer.recognize_google(audio)
                print(f"Heard: {text}")
                
                # Classify and send command immediately  
                command = classify_intent(text)
                command_queue.put(command)
                
                # Set interrupt for immediate commands
                if command.type.value in ["stop", "deep_dive"]:
                    interrupt_event.set()
                    shared_state['interrupt_requested'] = True
                    
            except sr.UnknownValueError:
                pass  # Ignore unrecognized speech
                
        except sr.WaitTimeoutError:
            pass  # Continue listening
        except Exception as e:
            print(f"Listener error: {e}")
            time.sleep(0.1)

def start_listener_process(ipc_manager):
    """Start the voice listener in a separate process."""
    process = mp.Process(
        target=voice_listener_worker,
        args=(ipc_manager.command_queue, ipc_manager.interrupt_event, ipc_manager.shared_state)
    )
    process.daemon = True
    process.start()
    return process