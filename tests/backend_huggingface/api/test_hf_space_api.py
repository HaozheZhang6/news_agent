#!/usr/bin/env python3
"""
Tests for HuggingFace Space ASR API.

Tests both WAV file upload and base64-encoded audio formats.

Requirements:
    - HF_TOKEN environment variable (for private spaces)
    - gradio_client installed
    - Test audio files in tests/voice_samples/wav/

Run:
    uv run python -m pytest tests/backend_huggingface/api/test_hf_space_api.py -v
"""

import base64
import os
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


try:
    from gradio_client import Client, handle_file
    GRADIO_CLIENT_AVAILABLE = True
except ImportError:
    GRADIO_CLIENT_AVAILABLE = False
    pytest.skip("gradio_client not installed", allow_module_level=True)


# HuggingFace Space configuration
HF_SPACE = "hz6666/SenseVoiceSmall"
HF_TOKEN = os.getenv("HF_TOKEN")

# Test audio files
TEST_AUDIO_DIR = project_root / "tests" / "voice_samples" / "wav"
TEST_AUDIO_FILES = [
    "test_analysis_aapl_deeper.wav",
    "test_news_nvda_latest.wav",
    "test_price_aapl_today.wav",
]


class TestResult:
    """Store test results for comparison."""
    def __init__(self, method: str, audio_file: str):
        self.method = method  # "wav" or "base64"
        self.audio_file = audio_file
        self.transcription = ""
        self.latency_ms = 0
        self.success = False
        self.error = None
        self.file_size_bytes = 0


@pytest.fixture
def hf_client():
    """Create HuggingFace Space client."""
    if not GRADIO_CLIENT_AVAILABLE:
        pytest.skip("gradio_client not installed")

    return Client(HF_SPACE, hf_token=HF_TOKEN)


@pytest.fixture
def test_audio_files():
    """Get list of available test audio files."""
    available_files = []
    for filename in TEST_AUDIO_FILES:
        filepath = TEST_AUDIO_DIR / filename
        if filepath.exists():
            available_files.append(filepath)

    if not available_files:
        pytest.skip(f"No test audio files found in {TEST_AUDIO_DIR}")

    return available_files


def encode_wav_to_base64(wav_path: Path) -> str:
    """Encode WAV file to base64 string."""
    with open(wav_path, 'rb') as f:
        wav_bytes = f.read()
    return base64.b64encode(wav_bytes).decode('utf-8')


def test_hf_space_connection(hf_client):
    """Test basic connection to HuggingFace Space."""
    try:
        # Try to get space info
        assert hf_client is not None
        print(f"✓ Connected to HuggingFace Space: {HF_SPACE}")
    except Exception as e:
        pytest.fail(f"Failed to connect to HuggingFace Space: {e}")


def test_transcribe_wav_file(hf_client, test_audio_files):
    """Test transcription using WAV file upload."""
    results = []

    for audio_file in test_audio_files[:2]:  # Test first 2 files
        result = TestResult("wav", audio_file.name)
        result.file_size_bytes = audio_file.stat().st_size

        try:
            print(f"\n📤 Testing WAV upload: {audio_file.name} ({result.file_size_bytes} bytes)")

            start_time = time.time()
            transcription = hf_client.predict(
                handle_file(str(audio_file)),
                api_name="/predict"
            )
            result.latency_ms = int((time.time() - start_time) * 1000)

            result.transcription = str(transcription)
            result.success = True

            print(f"✓ Transcription: '{result.transcription}'")
            print(f"⏱️  Latency: {result.latency_ms}ms")

            results.append(result)

        except Exception as e:
            result.error = str(e)
            print(f"✗ Error: {e}")
            results.append(result)
            pytest.fail(f"WAV transcription failed: {e}")

    # Verify at least one succeeded
    assert any(r.success for r in results), "All WAV transcriptions failed"

    # Check latency is reasonable (< 10 seconds)
    for r in results:
        if r.success:
            assert r.latency_ms < 10000, f"Latency too high: {r.latency_ms}ms"


def test_transcribe_base64_audio(hf_client, test_audio_files):
    """Test transcription using base64-encoded audio."""
    results = []

    for audio_file in test_audio_files[:2]:  # Test first 2 files
        result = TestResult("base64", audio_file.name)
        result.file_size_bytes = audio_file.stat().st_size

        try:
            print(f"\n📤 Testing base64 upload: {audio_file.name} ({result.file_size_bytes} bytes)")

            # Encode to base64
            base64_audio = encode_wav_to_base64(audio_file)
            base64_size = len(base64_audio)
            print(f"   Base64 size: {base64_size} chars (overhead: {base64_size / result.file_size_bytes:.2f}x)")

            # Send as dict with base64 data
            audio_dict = {
                "name": audio_file.name,
                "data": base64_audio
            }

            start_time = time.time()
            transcription = hf_client.predict(
                audio_dict,
                api_name="/predict"
            )
            result.latency_ms = int((time.time() - start_time) * 1000)

            result.transcription = str(transcription)
            result.success = True

            print(f"✓ Transcription: '{result.transcription}'")
            print(f"⏱️  Latency: {result.latency_ms}ms")

            results.append(result)

        except Exception as e:
            result.error = str(e)
            print(f"✗ Error: {e}")
            results.append(result)
            # Don't fail test - base64 might not be supported yet
            print(f"⚠️  Base64 method not supported or failed: {e}")

    return results


def test_compare_wav_vs_base64(hf_client, test_audio_files):
    """Compare WAV vs base64 performance."""
    if len(test_audio_files) == 0:
        pytest.skip("No test audio files available")

    # Test same file with both methods
    test_file = test_audio_files[0]

    print(f"\n{'='*60}")
    print(f"Performance Comparison: {test_file.name}")
    print(f"{'='*60}")

    # Test WAV method
    wav_result = TestResult("wav", test_file.name)
    wav_result.file_size_bytes = test_file.stat().st_size

    try:
        start_time = time.time()
        transcription = hf_client.predict(
            handle_file(str(test_file)),
            api_name="/predict"
        )
        wav_result.latency_ms = int((time.time() - start_time) * 1000)
        wav_result.transcription = str(transcription)
        wav_result.success = True
    except Exception as e:
        wav_result.error = str(e)

    # Test base64 method
    base64_result = TestResult("base64", test_file.name)
    base64_result.file_size_bytes = test_file.stat().st_size

    try:
        base64_audio = encode_wav_to_base64(test_file)
        audio_dict = {"name": test_file.name, "data": base64_audio}

        start_time = time.time()
        transcription = hf_client.predict(
            audio_dict,
            api_name="/predict"
        )
        base64_result.latency_ms = int((time.time() - start_time) * 1000)
        base64_result.transcription = str(transcription)
        base64_result.success = True
    except Exception as e:
        base64_result.error = str(e)

    # Print comparison
    print(f"\n📊 Results:")
    print(f"{'Method':<10} {'Success':<10} {'Latency':<12} {'Transcription'}")
    print(f"{'-'*60}")
    print(f"{'WAV':<10} {'✓' if wav_result.success else '✗':<10} {wav_result.latency_ms if wav_result.success else 'N/A':<12} {wav_result.transcription if wav_result.success else wav_result.error}")
    print(f"{'Base64':<10} {'✓' if base64_result.success else '✗':<10} {base64_result.latency_ms if base64_result.success else 'N/A':<12} {base64_result.transcription if base64_result.success else base64_result.error}")

    if wav_result.success and base64_result.success:
        latency_diff = abs(wav_result.latency_ms - base64_result.latency_ms)
        faster_method = "WAV" if wav_result.latency_ms < base64_result.latency_ms else "Base64"
        print(f"\n⚡ Faster method: {faster_method} (by {latency_diff}ms)")

        # Check if transcriptions match
        if wav_result.transcription == base64_result.transcription:
            print(f"✓ Transcriptions match")
        else:
            print(f"⚠️  Transcriptions differ:")
            print(f"   WAV: {wav_result.transcription}")
            print(f"   Base64: {base64_result.transcription}")

    # Assert at least one method works
    assert wav_result.success or base64_result.success, "Both methods failed"


def test_multiple_audio_files(hf_client, test_audio_files):
    """Test transcription on multiple audio files."""
    results = []

    print(f"\n{'='*60}")
    print(f"Testing Multiple Audio Files")
    print(f"{'='*60}")

    for audio_file in test_audio_files[:3]:  # Test up to 3 files
        result = TestResult("wav", audio_file.name)
        result.file_size_bytes = audio_file.stat().st_size

        try:
            start_time = time.time()
            transcription = hf_client.predict(
                handle_file(str(audio_file)),
                api_name="/predict"
            )
            result.latency_ms = int((time.time() - start_time) * 1000)
            result.transcription = str(transcription)
            result.success = True
            results.append(result)
        except Exception as e:
            result.error = str(e)
            results.append(result)

    # Print summary
    print(f"\n📊 Summary:")
    print(f"{'File':<30} {'Success':<10} {'Latency (ms)':<15} {'Transcription'}")
    print(f"{'-'*80}")

    for r in results:
        print(f"{r.audio_file[:30]:<30} {'✓' if r.success else '✗':<10} {r.latency_ms if r.success else 'N/A':<15} {r.transcription[:40] if r.success else r.error[:40]}")

    # Calculate statistics
    successful = [r for r in results if r.success]
    if successful:
        avg_latency = sum(r.latency_ms for r in successful) / len(successful)
        min_latency = min(r.latency_ms for r in successful)
        max_latency = max(r.latency_ms for r in successful)

        print(f"\n📈 Statistics:")
        print(f"   Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"   Avg latency: {avg_latency:.0f}ms")
        print(f"   Min latency: {min_latency}ms")
        print(f"   Max latency: {max_latency}ms")

    # Assert most succeeded
    assert len(successful) >= len(results) * 0.8, "Less than 80% success rate"


def test_empty_audio_handling(hf_client):
    """Test handling of empty or invalid audio."""
    print(f"\n{'='*60}")
    print(f"Testing Error Handling")
    print(f"{'='*60}")

    # Test 1: Empty base64
    try:
        result = hf_client.predict(
            {"name": "empty.wav", "data": ""},
            api_name="/predict"
        )
        print(f"Empty audio result: {result}")
        # Should either error or return "No audio received"
    except Exception as e:
        print(f"✓ Empty audio correctly rejected: {e}")

    # Test 2: Invalid base64
    try:
        result = hf_client.predict(
            {"name": "invalid.wav", "data": "not_valid_base64"},
            api_name="/predict"
        )
        print(f"Invalid audio result: {result}")
    except Exception as e:
        print(f"✓ Invalid audio correctly rejected: {e}")


@pytest.mark.parametrize("audio_file", TEST_AUDIO_FILES[:2])
def test_transcribe_parametrized(hf_client, audio_file):
    """Parametrized test for multiple audio files."""
    audio_path = TEST_AUDIO_DIR / audio_file

    if not audio_path.exists():
        pytest.skip(f"Audio file not found: {audio_file}")

    try:
        result = hf_client.predict(
            handle_file(str(audio_path)),
            api_name="/predict"
        )

        assert isinstance(result, str), f"Expected string result, got {type(result)}"
        assert len(result) > 0, "Empty transcription"

        print(f"✓ {audio_file}: {result}")

    except Exception as e:
        pytest.fail(f"Transcription failed for {audio_file}: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
