import threading
import queue
import time

# Ensure 'sr' symbol exists for tests to patch
try:
    import speech_recognition as sr  # type: ignore
except Exception:  # pragma: no cover
    sr = None  # type: ignore

class VoiceListener:
    def __init__(self, command_queue: queue.Queue):
        self.recognizer = sr.Recognizer()
        self.command_queue = command_queue
        self._stop_event = threading.Event()
        self._thread = None

    def _listen_loop(self):
        if sr is None:
            return

        mic = sr.Microphone()
        source = mic.__enter__() if hasattr(mic, "__enter__") else mic
        try:
            self.recognizer.adjust_for_ambient_noise(source) # Adjust for ambient noise once
            print("VoiceListener: Adjusting for ambient noise...")
            time.sleep(1) # Give it a moment to adjust
            print("VoiceListener: Listening in background...")

            while not self._stop_event.is_set():
                try:
                    # Listen for audio for a short duration to allow for interruption
                    audio = self.recognizer.listen(source, phrase_time_limit=5) # Listen for up to 5 seconds
                    if self._stop_event.is_set():
                        break # Check stop event again after listening

                    print("VoiceListener: Recognizing...")
                    command = self.recognizer.recognize_google(audio, language='en-us')
                    print(f"VoiceListener: User said: {command}")
                    self.command_queue.put(command)
                except sr.UnknownValueError:
                    # print("VoiceListener: Could not understand audio")
                    pass # Ignore if nothing is understood, keep listening
                except sr.RequestError as e:
                    print(f"VoiceListener: Could not request results from Google Speech Recognition service; {e}")
                except Exception as e:
                    print(f"VoiceListener: An unexpected error occurred: {e}")
        finally:
            if hasattr(mic, "__exit__"):
                try:
                    mic.__exit__(None, None, None)
                except Exception:
                    pass

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._listen_loop)
            self._thread.daemon = True # Allow main program to exit even if thread is still running
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join() # Wait for the thread to finish
        print("VoiceListener: Stopped.")