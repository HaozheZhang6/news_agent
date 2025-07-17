import asyncio
import edge_tts
import pygame
import tempfile
import os

# Initialize pygame mixer
pygame.mixer.init()

# Global variable to hold the current sound object for interruption
current_sound = None

async def say(text: str, interrupt_event: asyncio.Event = None):
    """Converts text to speech using Edge-TTS and plays it. 
    Can be interrupted by setting the interrupt_event.
    """
    global current_sound

    # Use a temporary file for the audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        filepath = tmpfile.name

    try:
        # Generate speech using edge-tts
        communicate = edge_tts.Communicate(text, "en-US-JennyNeural") # Using a peaceful voice
        await communicate.save(filepath)

        # Load and play the audio with pygame
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()

        # Keep playing until finished or interrupted
        while pygame.mixer.music.get_busy():
            if interrupt_event and interrupt_event.is_set():
                pygame.mixer.music.stop()
                print("Speech interrupted.")
                break
            await asyncio.sleep(0.1) # Small delay to prevent busy-waiting

    except Exception as e:
        print(f"Error during speech synthesis or playback: {e}")
    finally:
        # Ensure the temporary file is deleted
        if os.path.exists(filepath):
            os.remove(filepath)

def stop_speaking():
    """Stops the current speech playback immediately."""
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
        print("Speech stopped by external command.")