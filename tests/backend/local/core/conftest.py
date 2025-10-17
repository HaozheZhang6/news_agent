"""Shared fixtures for backend core tests."""
import pytest
from pathlib import Path


# Test audio samples directory
TESTS_DIR = Path(__file__).parent.parent.parent.parent
AUDIO_DIR = TESTS_DIR / "voice_samples" / "wav"


@pytest.fixture
def audio_samples():
    """Load all WAV test audio samples."""
    samples = {}
    if AUDIO_DIR.exists():
        for wav_file in AUDIO_DIR.glob("*.wav"):
            with open(wav_file, 'rb') as f:
                samples[wav_file.stem] = f.read()
    return samples
