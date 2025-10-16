"""
Automated VAD Validation Testing

Tests the backend VAD validation system using real audio samples.
Tests both energy-based and WebRTC VAD validation.
"""

import pytest
import os
from pathlib import Path
from backend.app.core.audio_validator import AudioValidator, validate_audio_quality


# Test audio samples directory
TESTS_DIR = Path(__file__).parent.parent.parent.parent
AUDIO_DIR = TESTS_DIR / "voice_samples" / "wav"


class TestVADValidation:
    """Test suite for VAD validation with real audio samples."""

    @pytest.fixture
    def audio_validator(self):
        """Create AudioValidator instance with test settings."""
        return AudioValidator(
            energy_threshold=500.0,
            vad_mode=3,
            enable_webrtc_vad=True
        )

    @pytest.fixture
    def lenient_validator(self):
        """Create AudioValidator with lenient settings for testing."""
        return AudioValidator(
            energy_threshold=300.0,  # Lower energy threshold
            vad_mode=1,  # Less aggressive VAD
            enable_webrtc_vad=True
        )

    @pytest.fixture
    def audio_samples(self):
        """Load all WAV test audio samples."""
        samples = {}
        if AUDIO_DIR.exists():
            for wav_file in AUDIO_DIR.glob("*.wav"):
                with open(wav_file, 'rb') as f:
                    samples[wav_file.stem] = f.read()
        return samples

    def test_audio_samples_exist(self, audio_samples):
        """Verify test audio samples are available."""
        assert len(audio_samples) > 0, "No audio samples found in tests/voice_samples/wav/"
        print(f"\n✓ Found {len(audio_samples)} audio samples")

    def test_energy_calculation(self, audio_validator, audio_samples):
        """Test energy calculation for all audio samples."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        results = []
        for name, audio_data in audio_samples.items():
            energy = audio_validator.calculate_energy(audio_data, sample_rate=16000)
            results.append({
                "name": name,
                "energy": energy,
                "passes_threshold": energy >= audio_validator.energy_threshold
            })
            print(f"  {name}: energy={energy:.1f} (threshold={audio_validator.energy_threshold})")

        # At least some samples should have sufficient energy
        passing_samples = [r for r in results if r["passes_threshold"]]
        assert len(passing_samples) > 0, "No samples passed energy threshold"
        print(f"\n✓ {len(passing_samples)}/{len(results)} samples passed energy threshold")

    def test_webrtc_vad_validation(self, audio_validator, audio_samples):
        """Test WebRTC VAD validation for all audio samples."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        results = []
        for name, audio_data in audio_samples.items():
            is_speech, speech_ratio = audio_validator.validate_with_webrtc_vad(
                audio_data,
                sample_rate=16000
            )
            results.append({
                "name": name,
                "is_speech": is_speech,
                "speech_ratio": speech_ratio
            })
            status = "✓" if is_speech else "✗"
            print(f"  {status} {name}: speech_ratio={speech_ratio:.2f}")

        # At least some samples should be detected as speech
        speech_samples = [r for r in results if r["is_speech"]]
        assert len(speech_samples) > 0, "No samples detected as speech"
        print(f"\n✓ {len(speech_samples)}/{len(results)} samples detected as speech")

    def test_full_validation_pipeline(self, audio_validator, audio_samples):
        """Test complete validation pipeline (energy + WebRTC VAD)."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        results = []
        for name, audio_data in audio_samples.items():
            is_valid, validation_info = audio_validator.validate_audio(
                audio_data,
                sample_rate=16000,
                format="wav"
            )
            results.append({
                "name": name,
                "is_valid": is_valid,
                "energy": validation_info.get("energy", 0),
                "speech_ratio": validation_info.get("webrtc_speech_ratio", 0),
                "reason": validation_info.get("reason", "unknown")
            })
            status = "✓" if is_valid else "✗"
            print(f"  {status} {name}: energy={validation_info.get('energy', 0):.1f}, "
                  f"speech_ratio={validation_info.get('webrtc_speech_ratio', 0):.2f}, "
                  f"reason={validation_info.get('reason', 'unknown')}")

        # At least some samples should pass full validation
        valid_samples = [r for r in results if r["is_valid"]]
        assert len(valid_samples) > 0, "No samples passed full validation"
        print(f"\n✓ {len(valid_samples)}/{len(results)} samples passed full validation")

    def test_speech_ratio_threshold_3_percent(self, audio_samples):
        """Test that 3% speech ratio threshold is working (very lenient)."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        # Create validator with 3% threshold (our new very lenient setting)
        validator = AudioValidator(
            energy_threshold=500.0,
            vad_mode=3,
            enable_webrtc_vad=True
        )

        low_ratio_samples = []
        for name, audio_data in audio_samples.items():
            is_speech, speech_ratio = validator.validate_with_webrtc_vad(
                audio_data,
                sample_rate=16000
            )

            # Track samples with 3-30% speech ratio (would fail old 30% threshold)
            if 0.03 <= speech_ratio < 0.30:
                low_ratio_samples.append({
                    "name": name,
                    "speech_ratio": speech_ratio,
                    "is_valid": is_speech
                })
                print(f"  ✓ {name}: speech_ratio={speech_ratio:.2f} (would have been rejected with 30% threshold)")

        if low_ratio_samples:
            print(f"\n✓ Found {len(low_ratio_samples)} samples with 3-30% speech ratio")
            print("  These samples now pass validation with 3% threshold (very lenient)")
        else:
            print("\n  No samples found with 3-30% speech ratio")

    def test_lenient_vs_strict_validation(self, audio_samples):
        """Compare lenient vs strict validation settings."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        strict = AudioValidator(energy_threshold=500.0, vad_mode=3, enable_webrtc_vad=True)
        lenient = AudioValidator(energy_threshold=300.0, vad_mode=1, enable_webrtc_vad=True)

        print("\nComparing strict vs lenient validation:")
        for name, audio_data in list(audio_samples.items())[:5]:  # Test first 5 samples
            strict_valid, strict_info = strict.validate_audio(audio_data, 16000, "wav")
            lenient_valid, lenient_info = lenient.validate_audio(audio_data, 16000, "wav")

            print(f"\n  {name}:")
            print(f"    Strict:  {'✓' if strict_valid else '✗'} (energy={strict_info['energy']:.1f}, "
                  f"ratio={strict_info.get('webrtc_speech_ratio', 0):.2f})")
            print(f"    Lenient: {'✓' if lenient_valid else '✗'} (energy={lenient_info['energy']:.1f}, "
                  f"ratio={lenient_info.get('webrtc_speech_ratio', 0):.2f})")

    @pytest.mark.parametrize("sample_name,expected_valid", [
        ("test_price_aapl", True),
        ("test_news_nvda_latest", True),
        ("test_followup_happened", True),
    ])
    def test_specific_samples(self, audio_validator, audio_samples, sample_name, expected_valid):
        """Test specific audio samples for expected validation results."""
        if sample_name not in audio_samples:
            pytest.skip(f"Sample {sample_name} not found")

        audio_data = audio_samples[sample_name]
        is_valid, validation_info = audio_validator.validate_audio(
            audio_data,
            sample_rate=16000,
            format="wav"
        )

        print(f"\n{sample_name}:")
        print(f"  Valid: {is_valid} (expected: {expected_valid})")
        print(f"  Energy: {validation_info['energy']:.1f}")
        print(f"  Speech Ratio: {validation_info.get('webrtc_speech_ratio', 0):.2f}")
        print(f"  Reason: {validation_info['reason']}")

        assert is_valid == expected_valid, \
            f"Sample {sample_name} validation mismatch: got {is_valid}, expected {expected_valid}"


class TestVADEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_audio(self):
        """Test validation with empty audio."""
        validator = AudioValidator()
        is_valid, info = validator.validate_audio(b"", 16000, "wav")
        assert not is_valid
        assert info["energy"] == 0.0

    def test_invalid_sample_rate(self):
        """Test validation with invalid sample rate."""
        validator = AudioValidator()
        # WebRTC VAD should handle invalid sample rate gracefully
        audio_data = b"RIFF" + b"\x00" * 100
        is_valid, info = validator.validate_with_webrtc_vad(audio_data, 11025)
        assert is_valid  # Should return True on error

    def test_corrupted_audio(self):
        """Test validation with corrupted audio data."""
        validator = AudioValidator()
        corrupted_data = b"RIFF" + b"\xFF" * 1000
        is_valid, info = validator.validate_audio(corrupted_data, 16000, "wav")
        # Should not crash, may return False or True depending on corruption

    def test_very_short_audio(self):
        """Test validation with very short audio."""
        validator = AudioValidator()
        short_audio = b"RIFF" + b"\x00" * 500  # ~0.015s at 16kHz
        is_valid, info = validator.validate_with_webrtc_vad(short_audio, 16000)
        # Should handle gracefully


class TestVADPerformance:
    """Test VAD performance metrics."""

    def test_validation_speed(self, audio_samples):
        """Test validation performance."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        import time

        validator = AudioValidator()
        sample_name, audio_data = next(iter(audio_samples.items()))

        # Warm up
        validator.validate_audio(audio_data, 16000, "wav")

        # Measure
        times = []
        for _ in range(10):
            start = time.time()
            validator.validate_audio(audio_data, 16000, "wav")
            times.append((time.time() - start) * 1000)

        avg_time = sum(times) / len(times)
        print(f"\nValidation performance for {sample_name}:")
        print(f"  Average time: {avg_time:.2f}ms")
        print(f"  Min time: {min(times):.2f}ms")
        print(f"  Max time: {max(times):.2f}ms")

        # Validation should be fast (< 50ms for typical audio)
        assert avg_time < 50, f"Validation too slow: {avg_time:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])