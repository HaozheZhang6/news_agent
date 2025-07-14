import pyttsx3

def say(text):
    """Converts text to speech and speaks it out."""
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
