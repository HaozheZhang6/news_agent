"""
Tests for Audio Validator (WebRTC VAD and Energy Detection)
"""

import pytest
import numpy as np
from backend.app.core.audio_validator import (
    AudioValidator,
    get_audio_validator,
    validate_audio_quality,
)


class TestAudioValidator:
    """Test AudioValidator class."""

    def test_init_default(self):
        """Test default initialization."""
        validator = AudioValidator()
        assert validator.energy_threshold == 500.0
        assert validator.vad_mode == 3
        # enable_webrtc_vad depends on whether webrtcvad is available
        assert isinstance(validator.enable_webrtc_vad, bool)

    def test_init_custom(self):
        """Test custom initialization."""
        validator = AudioValidator(
            energy_threshold=300.0,
            vad_mode=1,
            enable_webrtc_vad=False
        )
        assert validator.energy_threshold == 300.0
        assert validator.vad_mode == 1
        assert validator.enable_webrtc_vad is False

    def test_vad_mode_clamping(self):
        """Test VAD mode is clamped to 0-3."""
        validator = AudioValidator(vad_mode=10)
        assert validator.vad_mode == 3

        validator = AudioValidator(vad_mode=-5)
        assert validator.vad_mode == 0

    def test_calculate_energy_silence(self):
        """Test energy calculation for silence."""
        validator = AudioValidator()

        # Create 1 second of silence (16-bit PCM)
        silence = np.zeros(16000, dtype=np.int16)
        wav_header = self._create_wav_header(len(silence) * 2)
        audio_bytes = wav_header + silence.tobytes()

        energy = validator.calculate_energy(audio_bytes, sample_rate=16000)
        assert energy == 0.0

    def test_calculate_energy_noise(self):
        """Test energy calculation for noise."""
        validator = AudioValidator()

        # Create 1 second of random noise
        noise = np.random.randint(-1000, 1000, 16000, dtype=np.int16)
        wav_header = self._create_wav_header(len(noise) * 2)
        audio_bytes = wav_header + noise.tobytes()

        energy = validator.calculate_energy(audio_bytes, sample_rate=16000)

        # Noise should have measurable energy
        assert energy > 0
        assert 200 < energy < 2000  # Typical range for this noise level

    def test_calculate_energy_speech(self):
        """Test energy calculation for simulated speech."""
        validator = AudioValidator()

        # Create 1 second of simulated speech (sine wave)
        t = np.linspace(0, 1, 16000)
        speech = (np.sin(2 * np.pi * 200 * t) * 5000).astype(np.int16)
        wav_header = self._create_wav_header(len(speech) * 2)
        audio_bytes = wav_header + speech.tobytes()

        energy = validator.calculate_energy(audio_bytes, sample_rate=16000)

        # Speech should have high energy
        assert energy > 1000

    def test_validate_audio_insufficient_energy(self):
        """Test audio validation rejects low energy audio."""
        validator = AudioValidator(energy_threshold=500.0)

        # Create low energy audio
        low_energy = np.random.randint(-100, 100, 16000, dtype=np.int16)
        wav_header = self._create_wav_header(len(low_energy) * 2)
        audio_bytes = wav_header + low_energy.tobytes()

        is_valid, info = validator.validate_audio(audio_bytes, sample_rate=16000)

        assert is_valid is False
        assert info['reason'] == 'insufficient_energy'
        assert info['energy'] < 500.0

    def test_validate_audio_sufficient_energy(self):
        """Test audio validation accepts high energy audio."""
        validator = AudioValidator(
            energy_threshold=500.0,
            enable_webrtc_vad=False  # Disable WebRTC VAD for this test
        )

        # Create high energy audio
        high_energy = np.random.randint(-5000, 5000, 16000, dtype=np.int16)
        wav_header = self._create_wav_header(len(high_energy) * 2)
        audio_bytes = wav_header + high_energy.tobytes()

        is_valid, info = validator.validate_audio(audio_bytes, sample_rate=16000)

        assert is_valid is True
        assert info['energy'] > 500.0
        assert info['energy_valid'] is True

    def test_validate_audio_non_wav_format(self):
        """Test validation skips non-WAV formats."""
        validator = AudioValidator()

        # Any random bytes
        audio_bytes = b"random opus data"

        is_valid, info = validator.validate_audio(
            audio_bytes,
            sample_rate=16000,
            format="opus"
        )

        # Should skip validation for non-WAV
        assert is_valid is True
        assert info['reason'] == 'format_not_wav'

    def test_webrtc_vad_validation(self):
        """Test WebRTC VAD integration."""
        validator = AudioValidator(
            energy_threshold=100.0,  # Low threshold
            vad_mode=3,
            enable_webrtc_vad=True
        )

        # Create speech-like audio (high energy, periodic)
        t = np.linspace(0, 1, 16000)
        speech = (np.sin(2 * np.pi * 200 * t) * 8000).astype(np.int16)
        wav_header = self._create_wav_header(len(speech) * 2)
        audio_bytes = wav_header + speech.tobytes()

        is_valid, info = validator.validate_audio(audio_bytes, sample_rate=16000)

        # Should pass energy check
        assert info['energy_valid'] is True

        # WebRTC VAD result depends on implementation
        # At minimum, should have attempted validation
        assert 'webrtc_speech_ratio' in info

    def test_singleton_pattern(self):
        """Test singleton pattern for get_audio_validator."""
        validator1 = get_audio_validator()
        validator2 = get_audio_validator()

        # Should return same instance
        assert validator1 is validator2

    def test_convenience_function(self):
        """Test validate_audio_quality convenience function."""
        # Create high energy audio
        high_energy = np.random.randint(-5000, 5000, 16000, dtype=np.int16)
        wav_header = self._create_wav_header(len(high_energy) * 2)
        audio_bytes = wav_header + high_energy.tobytes()

        is_valid, info = validate_audio_quality(
            audio_bytes,
            sample_rate=16000,
            format="wav",
            energy_threshold=500.0,
            vad_mode=3
        )

        assert isinstance(is_valid, bool)
        assert isinstance(info, dict)
        assert 'energy' in info
        assert 'reason' in info

    @staticmethod
    def _create_wav_header(data_size: int) -> bytes:
        """Create a simple WAV header."""
        import struct

        # WAV header structure
        header = b'RIFF'
        header += struct.pack('<I', 36 + data_size)  # File size - 8
        header += b'WAVE'
        header += b'fmt '
        header += struct.pack('<I', 16)  # Subchunk1 size (PCM)
        header += struct.pack('<H', 1)   # Audio format (PCM)
        header += struct.pack('<H', 1)   # Num channels (mono)
        header += struct.pack('<I', 16000)  # Sample rate
        header += struct.pack('<I', 32000)  # Byte rate (16000 * 1 * 2)
        header += struct.pack('<H', 2)   # Block align (1 * 2)
        header += struct.pack('<H', 16)  # Bits per sample
        header += b'data'
        header += struct.pack('<I', data_size)  # Data size

        return header


class TestAudioValidatorEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_audio(self):
        """Test handling of empty audio."""
        validator = AudioValidator()

        wav_header = self._create_wav_header(0)
        audio_bytes = wav_header

        energy = validator.calculate_energy(audio_bytes, sample_rate=16000)
        assert energy == 0.0

    def test_invalid_audio_bytes(self):
        """Test handling of invalid audio data."""
        validator = AudioValidator()

        # Random bytes that don't represent valid audio
        audio_bytes = b"not valid audio data"

        # Should handle gracefully without crashing
        energy = validator.calculate_energy(audio_bytes, sample_rate=16000)
        assert energy >= 0.0  # Should return non-negative value

    def test_different_sample_rates(self):
        """Test validation with different sample rates."""
        validator = AudioValidator(enable_webrtc_vad=False)

        for sample_rate in [8000, 16000, 32000, 48000]:
            # Create audio at specific sample rate
            audio = np.random.randint(-5000, 5000, sample_rate, dtype=np.int16)
            wav_header = self._create_wav_header(len(audio) * 2)
            audio_bytes = wav_header + audio.tobytes()

            energy = validator.calculate_energy(audio_bytes, sample_rate=sample_rate)
            assert energy > 0

    @staticmethod
    def _create_wav_header(data_size: int) -> bytes:
        """Create a simple WAV header."""
        import struct

        header = b'RIFF'
        header += struct.pack('<I', 36 + data_size)
        header += b'WAVE'
        header += b'fmt '
        header += struct.pack('<I', 16)
        header += struct.pack('<H', 1)
        header += struct.pack('<H', 1)
        header += struct.pack('<I', 16000)
        header += struct.pack('<I', 32000)
        header += struct.pack('<H', 2)
        header += struct.pack('<H', 16)
        header += b'data'
        header += struct.pack('<I', data_size)

        return header


@pytest.mark.benchmark
class TestAudioValidatorPerformance:
    """Test performance of audio validation."""

    def test_energy_calculation_performance(self, benchmark):
        """Benchmark energy calculation."""
        validator = AudioValidator()

        # 3 seconds of audio
        audio = np.random.randint(-5000, 5000, 48000, dtype=np.int16)
        wav_header = self._create_wav_header(len(audio) * 2)
        audio_bytes = wav_header + audio.tobytes()

        # Should complete in < 5ms
        result = benchmark(validator.calculate_energy, audio_bytes, 16000)
        assert result > 0

    @staticmethod
    def _create_wav_header(data_size: int) -> bytes:
        """Create a simple WAV header."""
        import struct

        header = b'RIFF'
        header += struct.pack('<I', 36 + data_size)
        header += b'WAVE'
        header += b'fmt '
        header += struct.pack('<I', 16)
        header += struct.pack('<H', 1)
        header += struct.pack('<H', 1)
        header += struct.pack('<I', 16000)
        header += struct.pack('<I', 32000)
        header += struct.pack('<H', 2)
        header += struct.pack('<H', 16)
        header += b'data'
        header += struct.pack('<I', data_size)

        return header
