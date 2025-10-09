"""Audio logging utilities for saving voice inputs and TTS outputs."""
import os
import wave
from datetime import datetime
from pathlib import Path
try:
    from pydub import AudioSegment
except Exception:  # pragma: no cover - optional in CI
    class AudioSegment:  # minimal stub
        @staticmethod
        def from_wav(path: str):
            class _Seg:
                def export(self, *_args, **_kwargs):
                    return None

            return _Seg()

        @staticmethod
        def from_file(path: str):
            class _Seg:
                def export(self, *_args, **_kwargs):
                    return None

            return _Seg()
from .config import AUDIO_LOGS_DIR, OUTPUT_DIR, AUDIO_RATE, AUDIO_CHANNELS


class AudioLogger:
    def __init__(self):
        self.audio_file_count = 0
        
    def _wav_to_mp3(self, wav_path: Path, mp3_path: Path) -> None:
        """Convert WAV file to MP3 and remove original WAV."""
        audio_segment = AudioSegment.from_wav(str(wav_path))
        audio_segment.export(str(mp3_path), format="mp3")
        os.remove(str(wav_path))
        
    def _save_wav_data(self, wav_path: Path, audio_data: bytes) -> None:
        """Save raw audio data as WAV file."""
        with wave.open(str(wav_path), 'wb') as wf:
            wf.setnchannels(AUDIO_CHANNELS)
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(AUDIO_RATE)
            wf.writeframes(audio_data)
        
    def save_input_audio(self, audio_data: bytes, prefix="input") -> str:
        """Save raw audio data as MP3 file."""
        self.audio_file_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        wav_path = AUDIO_LOGS_DIR / f"{prefix}_{timestamp}_{self.audio_file_count}.wav"
        mp3_path = AUDIO_LOGS_DIR / f"{prefix}_{timestamp}_{self.audio_file_count}.mp3"
        
        self._save_wav_data(wav_path, audio_data)
        self._wav_to_mp3(wav_path, mp3_path)
        
        print(f"Audio saved: {mp3_path}")
        return str(mp3_path)
    
    def save_segments_audio(self, segments_to_save: list, prefix="input") -> str:
        """Save audio segments from the ASR-style recording."""
        if not segments_to_save:
            return ""
            
        self.audio_file_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        wav_path = AUDIO_LOGS_DIR / f"{prefix}_{timestamp}_{self.audio_file_count}.wav"
        mp3_path = AUDIO_LOGS_DIR / f"{prefix}_{timestamp}_{self.audio_file_count}.mp3"
        
        # Combine all audio segments
        audio_frames = [seg[0] for seg in segments_to_save]
        combined_audio = b''.join(audio_frames)
        
        self._save_wav_data(wav_path, combined_audio)
        self._wav_to_mp3(wav_path, mp3_path)
        
        print(f"Audio segments saved: {mp3_path}")
        return str(mp3_path)
    
    def save_response_audio(self, audio_path: str) -> str:
        """Copy and organize TTS response audio."""
        if not os.path.exists(audio_path):
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response_path = OUTPUT_DIR / f"response_{timestamp}_{self.audio_file_count}.mp3"
        
        # Copy the audio file to output directory
        audio_segment = AudioSegment.from_file(audio_path)
        audio_segment.export(str(response_path), format="mp3")
        
        print(f"Response audio saved: {response_path}")
        return str(response_path)
    
    def get_temp_wav_path(self) -> str:
        """Get temporary WAV file path for SenseVoice input."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(AUDIO_LOGS_DIR / f"temp_{timestamp}.wav")


# Global audio logger instance
audio_logger = AudioLogger()