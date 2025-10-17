"""Shared fixtures for integration tests."""
import pytest
import base64
from pathlib import Path


# Test audio samples directory
TESTS_DIR = Path(__file__).parent.parent
AUDIO_DIR = TESTS_DIR / "voice_samples" / "wav"


@pytest.fixture
def audio_samples():
    """Load test audio samples."""
    samples = {}
    if AUDIO_DIR.exists():
        for wav_file in list(AUDIO_DIR.glob("*.wav"))[:5]:
            with open(wav_file, 'rb') as f:
                raw_data = f.read()
            # Reset file pointer for base64 encoding
            samples[wav_file.stem] = {
                "raw": raw_data,
                "b64": base64.b64encode(raw_data).decode()
            }
    return samples
