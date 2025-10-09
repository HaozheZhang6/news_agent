class Vad:  # Minimal stub for test environment
    def __init__(self):
        self._mode = 0

    def set_mode(self, mode: int):
        self._mode = int(mode)

    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        # Return False for empty, True for any non-empty as a naive stub
        return bool(audio_chunk)


