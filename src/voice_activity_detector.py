"""Voice Activity Detection using WebRTC VAD."""
import webrtcvad
import time
from .config import VAD_MODE, AUDIO_RATE
from .conversation_logger import conversation_logger


class VoiceActivityDetector:
    def __init__(self, mode: int = VAD_MODE):
        """Initialize VAD with specified mode (0-3, higher = more sensitive)."""
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(mode)
        
    def check_vad_activity_conservative(self, audio_data: bytes, threshold_rate: float = 0.4) -> bool:
        """Conservative VAD check using 40% activation rate (same as ASR script 14).
        
        Args:
            audio_data: Raw audio bytes
            threshold_rate: Minimum percentage of frames that must contain speech (default 40%)
            
        Returns:
            bool: True if speech detected, False otherwise
        """
        try:
            num_speech_frames = 0
            step = int(AUDIO_RATE * 0.02)  # 20ms chunks
            flag_rate = round(threshold_rate * len(audio_data) // step)

            for i in range(0, len(audio_data), step):
                chunk = audio_data[i:i + step]
                if len(chunk) == step:
                    if self.vad.is_speech(chunk, sample_rate=AUDIO_RATE):
                        num_speech_frames += 1

            return num_speech_frames > flag_rate
            
        except Exception as e:
            conversation_logger.log_error(f"Conservative VAD processing failed: {e}")
            return False
        
    def check_vad_activity(self, audio_data: bytes, threshold_rate: float = 0.4) -> bool:
        """
        Check if audio contains speech using VAD.
        
        Args:
            audio_data: Raw audio bytes
            threshold_rate: Minimum percentage of frames that must contain speech
            
        Returns:
            bool: True if speech detected, False otherwise
        """
        try:
            num_speech_frames = 0
            total_frames = 0
            step = int(AUDIO_RATE * 0.02)  # 20ms chunks
            
            # Process audio in 20ms chunks
            for i in range(0, len(audio_data), step):
                chunk = audio_data[i:i + step]
                if len(chunk) == step:
                    total_frames += 1
                    if self.vad.is_speech(chunk, sample_rate=AUDIO_RATE):
                        num_speech_frames += 1
            
            if total_frames == 0:
                return False
                
            speech_rate = num_speech_frames / total_frames
            is_speech = speech_rate > threshold_rate
            
            # Log VAD results
            conversation_logger.log_vad_activity(is_speech, time.time())
            
            return is_speech
            
        except Exception as e:
            conversation_logger.log_error(f"VAD processing failed: {e}")
            return False
    
    def is_speech_frame(self, audio_chunk: bytes) -> bool:
        """Check if a single 20ms frame contains speech."""
        try:
            return self.vad.is_speech(audio_chunk, sample_rate=AUDIO_RATE)
        except Exception as e:
            conversation_logger.log_error(f"VAD frame check failed: {e}")
            return False


# Global VAD instance
vad_detector = VoiceActivityDetector()