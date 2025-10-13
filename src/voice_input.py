import threading
import queue
import time

# VoiceListener class is deprecated - use SenseVoice-based voice_listener_process instead
class VoiceListener:
    """Deprecated: Use SenseVoice-based voice_listener_process instead."""
    def __init__(self, command_queue: queue.Queue):
        self.command_queue = command_queue
        self._stop_event = threading.Event()
        self._thread = None
        print("WARNING: VoiceListener is deprecated. Use SenseVoice-based voice_listener_process instead.")

    def _listen_loop(self):
        print("VoiceListener: This class is deprecated. Please use SenseVoice-based voice_listener_process.")
        return

    def start(self):
        print("VoiceListener: This class is deprecated. Please use SenseVoice-based voice_listener_process.")
        return

    def stop(self):
        print("VoiceListener: This class is deprecated. Please use SenseVoice-based voice_listener_process.")
        return