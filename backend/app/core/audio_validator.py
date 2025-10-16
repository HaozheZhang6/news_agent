"""
Audio Validation Module

Provides audio quality validation using energy analysis and WebRTC VAD
to filter out noise and silence before sending to ASR.
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional
import logging

try:
    import webrtcvad
    WEBRTC_VAD_AVAILABLE = True
except ImportError:
    WEBRTC_VAD_AVAILABLE = False
    logging.warning("webrtcvad not available - WebRTC VAD validation disabled")


class AudioValidator:
    """Validates audio quality before ASR processing."""

    def __init__(
        self,
        energy_threshold: float = 500.0,
        vad_mode: int = 3,
        enable_webrtc_vad: bool = True,
        speech_ratio_threshold: float = 0.03
    ):
        """
        Initialize audio validator.

        Args:
            energy_threshold: RMS energy threshold for pre-filtering
            vad_mode: WebRTC VAD aggressiveness (0-3, 3 = most aggressive)
            enable_webrtc_vad: Enable WebRTC VAD validation
            speech_ratio_threshold: Minimum speech ratio (0.01-0.50, default 0.03)
        """
        self.energy_threshold = energy_threshold
        self.vad_mode = max(0, min(3, vad_mode))  # Clamp to 0-3
        self.enable_webrtc_vad = enable_webrtc_vad and WEBRTC_VAD_AVAILABLE
        self.speech_ratio_threshold = max(0.01, min(0.50, speech_ratio_threshold))  # Clamp to 0.01-0.50

        # Initialize WebRTC VAD if available
        self.vad = None
        if self.enable_webrtc_vad:
            try:
                self.vad = webrtcvad.Vad(self.vad_mode)
                logging.info(f"✅ WebRTC VAD initialized (mode={self.vad_mode})")
            except Exception as e:
                logging.warning(f"⚠️ Failed to initialize WebRTC VAD: {e}")
                self.vad = None

    def calculate_energy(self, audio_bytes: bytes, sample_rate: int = 16000) -> float:
        """
        Calculate RMS energy of audio signal.

        Args:
            audio_bytes: Raw audio bytes (WAV or PCM)
            sample_rate: Sample rate in Hz

        Returns:
            RMS energy value
        """
        try:
            # Skip WAV header if present (44 bytes)
            offset = 44 if len(audio_bytes) > 44 and audio_bytes[:4] == b'RIFF' else 0

            # Convert to numpy array (16-bit PCM)
            audio_array = np.frombuffer(audio_bytes[offset:], dtype=np.int16)

            if len(audio_array) == 0:
                return 0.0

            # Calculate RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_array.astype(float) ** 2))

            return float(rms)
        except Exception as e:
            logging.error(f"Error calculating audio energy: {e}")
            return 0.0

    def validate_with_webrtc_vad(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30
    ) -> Tuple[bool, float]:
        """
        Validate speech using WebRTC VAD.

        Args:
            audio_bytes: Raw audio bytes (must be PCM data)
            sample_rate: Sample rate (8000, 16000, 32000, or 48000 Hz)
            frame_duration_ms: Frame duration (10, 20, or 30 ms)

        Returns:
            Tuple of (is_speech, speech_ratio)
        """
        if not self.vad:
            return True, 1.0  # No VAD available, assume speech

        try:
            # Skip WAV header if present
            offset = 44 if len(audio_bytes) > 44 and audio_bytes[:4] == b'RIFF' else 0
            audio_data = audio_bytes[offset:]

            # WebRTC VAD requires specific sample rates
            if sample_rate not in [8000, 16000, 32000, 48000]:
                logging.warning(f"Invalid sample rate {sample_rate} for WebRTC VAD")
                return True, 1.0

            # Calculate frame size (bytes)
            # frame_size = (sample_rate × frame_duration_ms / 1000) × 2 bytes (16-bit)
            frame_size = int(sample_rate * frame_duration_ms / 1000) * 2

            if frame_size <= 0 or len(audio_data) < frame_size:
                return False, 0.0

            speech_frames = 0
            total_frames = 0

            # Process audio in frames
            for i in range(0, len(audio_data) - frame_size + 1, frame_size):
                frame = audio_data[i:i + frame_size]
                total_frames += 1

                try:
                    is_speech = self.vad.is_speech(frame, sample_rate)
                    if is_speech:
                        speech_frames += 1
                except Exception as e:
                    # Frame validation failed, skip
                    continue

            if total_frames == 0:
                return False, 0.0

            # Calculate speech ratio
            speech_ratio = speech_frames / total_frames

            # Use configurable speech ratio threshold
            # This allows adjustment based on use case (conversational vs. dictation)
            is_valid = speech_ratio >= self.speech_ratio_threshold

            return is_valid, speech_ratio

        except Exception as e:
            logging.error(f"WebRTC VAD error: {e}")
            return True, 1.0  # On error, assume valid

    def validate_audio(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        format: str = "wav"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate audio using two-stage validation:
        1. Energy-based pre-filtering (fast)
        2. WebRTC VAD validation (accurate)

        Args:
            audio_bytes: Audio data bytes
            sample_rate: Sample rate in Hz
            format: Audio format (wav, opus, webm, etc.)

        Returns:
            Tuple of (is_valid, validation_info)
        """
        validation_info = {
            "energy": 0.0,
            "energy_valid": False,
            "webrtc_valid": False,
            "webrtc_speech_ratio": 0.0,
            "reason": "unknown",
        }

        # Skip validation for non-WAV formats (already decoded by client)
        if format not in ["wav", "pcm"]:
            logging.info(f"Skipping validation for format: {format}")
            validation_info["reason"] = "format_not_wav"
            return True, validation_info

        # Stage 1: Energy-based pre-filtering (~1ms)
        energy = self.calculate_energy(audio_bytes, sample_rate)
        validation_info["energy"] = energy

        if energy < self.energy_threshold:
            validation_info["reason"] = "insufficient_energy"
            logging.info(f"🚫 Audio rejected: insufficient energy ({energy:.1f} < {self.energy_threshold})")
            return False, validation_info

        validation_info["energy_valid"] = True

        # Stage 2: WebRTC VAD validation (~5-10ms)
        if self.enable_webrtc_vad and self.vad:
            is_speech, speech_ratio = self.validate_with_webrtc_vad(
                audio_bytes,
                sample_rate=sample_rate
            )
            validation_info["webrtc_valid"] = is_speech
            validation_info["webrtc_speech_ratio"] = speech_ratio

            if not is_speech:
                validation_info["reason"] = "no_speech_detected"
                logging.info(
                    f"🚫 Audio rejected: WebRTC VAD failed "
                    f"(speech_ratio={speech_ratio:.2f})"
                )
                return False, validation_info

        # Both stages passed
        validation_info["reason"] = "valid"
        logging.info(
            f"✅ Audio validated: energy={energy:.1f}, "
            f"speech_ratio={validation_info['webrtc_speech_ratio']:.2f}"
        )
        return True, validation_info


# Singleton instance
_audio_validator: Optional[AudioValidator] = None


def get_audio_validator(
    energy_threshold: float = 500.0,
    vad_mode: int = 3,
    enable_webrtc_vad: bool = True,
    speech_ratio_threshold: float = 0.03
) -> AudioValidator:
    """Get or create singleton AudioValidator instance."""
    global _audio_validator

    if _audio_validator is None:
        _audio_validator = AudioValidator(
            energy_threshold=energy_threshold,
            vad_mode=vad_mode,
            enable_webrtc_vad=enable_webrtc_vad,
            speech_ratio_threshold=speech_ratio_threshold
        )

    return _audio_validator


def validate_audio_quality(
    audio_bytes: bytes,
    sample_rate: int = 16000,
    format: str = "wav",
    energy_threshold: float = 500.0,
    vad_mode: int = 3,
    enable_webrtc_vad: bool = True,
    speech_ratio_threshold: float = 0.03
) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to validate audio quality.

    Args:
        audio_bytes: Audio data bytes
        sample_rate: Sample rate in Hz
        format: Audio format
        energy_threshold: RMS energy threshold
        vad_mode: WebRTC VAD aggressiveness (0-3)
        enable_webrtc_vad: Enable WebRTC VAD
        speech_ratio_threshold: Minimum speech ratio (0.01-0.50)

    Returns:
        Tuple of (is_valid, validation_info)
    """
    validator = get_audio_validator(
        energy_threshold=energy_threshold,
        vad_mode=vad_mode,
        enable_webrtc_vad=enable_webrtc_vad,
        speech_ratio_threshold=speech_ratio_threshold
    )

    return validator.validate_audio(audio_bytes, sample_rate, format)
