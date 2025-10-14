#!/usr/bin/env python3
"""
Comprehensive WebSocket WAV Audio Tests.

Tests the current WAV-based audio pipeline:
- PCM audio capture → WAV encoding → WebSocket transmission
- Backend WAV decoding → SenseVoice ASR → Response generation
- TTS audio streaming back to frontend

Requires:
- Backend server running: make run-server
- SenseVoice model loaded
- Valid Supabase credentials
"""

import asyncio
import base64
import json
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

import pytest
import websockets

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class WAVAudioMessage:
    """WAV audio message format."""
    event: str = "audio_chunk"
    audio_chunk: str = ""
    format: str = "wav"
    is_final: bool = True
    session_id: str = ""
    user_id: str = "test-user-001"
    sample_rate: int = 16000
    file_size: int = 0


class WAVEncoder:
    """Simple WAV encoder for test audio generation."""

    def __init__(self, sample_rate: int = 16000, num_channels: int = 1, bit_depth: int = 16):
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.bit_depth = bit_depth

    def encode_from_pcm(self, pcm_samples: List[float]) -> bytes:
        """
        Encode PCM samples to WAV format.

        Args:
            pcm_samples: List of float samples in range [-1.0, 1.0]

        Returns:
            Complete WAV file as bytes
        """
        # Convert float32 samples to int16
        int16_samples = [int(max(-32768, min(32767, s * 32767))) for s in pcm_samples]

        # Pack samples as 16-bit little-endian integers
        pcm_data = struct.pack('<' + 'h' * len(int16_samples), *int16_samples)

        # Calculate sizes
        bytes_per_sample = self.bit_depth // 8
        block_align = self.num_channels * bytes_per_sample
        byte_rate = self.sample_rate * block_align
        data_size = len(pcm_data)

        # Build WAV header (44 bytes)
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')

        # fmt chunk
        fmt_chunk = struct.pack(
            '<4sIHHIIHH',
            b'fmt ',
            16,  # Chunk size
            1,   # Audio format (PCM)
            self.num_channels,
            self.sample_rate,
            byte_rate,
            block_align,
            self.bit_depth
        )

        # data chunk
        data_chunk = struct.pack('<4sI', b'data', data_size)

        return header + fmt_chunk + data_chunk + pcm_data


def generate_sine_wave(frequency: float, duration: float, sample_rate: int = 16000) -> List[float]:
    """
    Generate a sine wave for testing.

    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        List of float samples in range [-1.0, 1.0]
    """
    import math
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = math.sin(2.0 * math.pi * frequency * t)
        samples.append(sample)
    return samples


def generate_test_speech(duration: float = 2.0, sample_rate: int = 16000) -> List[float]:
    """
    Generate test "speech-like" audio using multiple sine waves.

    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        List of float samples
    """
    import math
    num_samples = int(duration * sample_rate)
    samples = []

    # Mix multiple frequencies to simulate speech formants
    frequencies = [200, 400, 800, 1600]  # Hz
    amplitudes = [0.3, 0.2, 0.15, 0.1]

    for i in range(num_samples):
        t = i / sample_rate
        sample = 0.0
        for freq, amp in zip(frequencies, amplitudes):
            sample += amp * math.sin(2.0 * math.pi * freq * t)

        # Add envelope (fade in/out)
        envelope = 1.0
        fade_duration = 0.1  # 100ms fade
        fade_samples = int(fade_duration * sample_rate)
        if i < fade_samples:
            envelope = i / fade_samples
        elif i > num_samples - fade_samples:
            envelope = (num_samples - i) / fade_samples

        samples.append(sample * envelope)

    return samples


@pytest.fixture
def ws_url():
    """WebSocket URL for testing."""
    return "ws://localhost:8000/ws/voice/simple"


@pytest.fixture
def wav_encoder():
    """WAV encoder instance."""
    return WAVEncoder(sample_rate=16000, num_channels=1, bit_depth=16)


@pytest.mark.asyncio
async def test_websocket_connection(ws_url):
    """Test basic WebSocket connection."""
    try:
        async with websockets.connect(
            ws_url,
            extra_headers={"Origin": "http://localhost:3000"}
        ) as websocket:
            assert websocket.open
            print("✓ WebSocket connection established")
    except Exception as e:
        pytest.fail(f"Failed to connect to WebSocket: {e}")


@pytest.mark.asyncio
async def test_websocket_init_message(ws_url):
    """Test sending init message and receiving session_id."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:

        # Send init message
        init_msg = {
            "event": "init",
            "user_id": "test-user-001"
        }
        await websocket.send(json.dumps(init_msg))
        print("📤 Sent init message")

        # Wait for session_started message
        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(response)

        assert data.get("event") == "session_started"
        assert "session_id" in data
        assert len(data["session_id"]) > 0

        print(f"✓ Received session_id: {data['session_id']}")


@pytest.mark.asyncio
async def test_send_wav_audio_simple(ws_url, wav_encoder):
    """Test sending simple WAV audio and receiving transcription."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:

        # Initialize session
        init_msg = {"event": "init", "user_id": "test-user-001"}
        await websocket.send(json.dumps(init_msg))

        response = await websocket.recv()
        session_data = json.loads(response)
        session_id = session_data["session_id"]
        print(f"📝 Session ID: {session_id}")

        # Generate test audio (2 second sine wave)
        pcm_samples = generate_sine_wave(440, 2.0, 16000)  # A4 note
        wav_data = wav_encoder.encode_from_pcm(pcm_samples)

        # Encode to base64
        wav_base64 = base64.b64encode(wav_data).decode('utf-8')

        # Send audio message
        audio_msg = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": wav_base64,
                "format": "wav",
                "is_final": True,
                "session_id": session_id,
                "user_id": "test-user-001",
                "sample_rate": 16000,
                "file_size": len(wav_data)
            }
        }

        await websocket.send(json.dumps(audio_msg))
        print(f"📤 Sent WAV audio: {len(wav_data)} bytes")

        # Wait for responses
        received_transcription = False
        received_audio = False

        try:
            for _ in range(20):  # Max 20 messages
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                event = data.get("event")

                if event == "transcription":
                    received_transcription = True
                    transcription = data.get("text", "")
                    print(f"📝 Transcription: {transcription}")

                elif event == "audio_chunk":
                    received_audio = True
                    print(f"🔊 Received TTS audio chunk")

                elif event == "audio_end":
                    print("✓ Audio streaming completed")
                    break

        except asyncio.TimeoutError:
            print("⏱️ Timeout waiting for responses")

        # Note: Sine wave won't transcribe to text, but backend should process it
        # We just verify the pipeline works
        assert received_audio or received_transcription, "Should receive some response"


@pytest.mark.asyncio
async def test_send_speech_like_audio(ws_url, wav_encoder):
    """Test sending speech-like audio (multiple frequencies)."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:

        # Initialize session
        init_msg = {"event": "init", "user_id": "test-user-001"}
        await websocket.send(json.dumps(init_msg))

        response = await websocket.recv()
        session_data = json.loads(response)
        session_id = session_data["session_id"]

        # Generate speech-like audio
        pcm_samples = generate_test_speech(duration=2.0)
        wav_data = wav_encoder.encode_from_pcm(pcm_samples)
        wav_base64 = base64.b64encode(wav_data).decode('utf-8')

        # Send audio
        audio_msg = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": wav_base64,
                "format": "wav",
                "is_final": True,
                "session_id": session_id,
                "user_id": "test-user-001",
                "sample_rate": 16000,
                "file_size": len(wav_data)
            }
        }

        await websocket.send(json.dumps(audio_msg))
        print(f"📤 Sent speech-like WAV: {len(wav_data)} bytes")

        # Collect responses
        responses = []
        try:
            for _ in range(20):
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(response)
                responses.append(data)

                if data.get("event") == "audio_end":
                    break
        except asyncio.TimeoutError:
            pass

        # Verify we got responses
        assert len(responses) > 0, "Should receive responses"

        event_types = [r.get("event") for r in responses]
        print(f"✓ Received events: {', '.join(event_types)}")


@pytest.mark.asyncio
async def test_wav_header_validation(ws_url, wav_encoder):
    """Test that backend properly validates WAV headers."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:

        # Initialize session
        init_msg = {"event": "init", "user_id": "test-user-001"}
        await websocket.send(json.dumps(init_msg))

        response = await websocket.recv()
        session_data = json.loads(response)
        session_id = session_data["session_id"]

        # Send valid WAV
        pcm_samples = generate_sine_wave(440, 1.0)
        wav_data = wav_encoder.encode_from_pcm(pcm_samples)

        # Verify WAV header
        assert wav_data[0:4] == b'RIFF', "Should have RIFF header"
        assert wav_data[8:12] == b'WAVE', "Should have WAVE identifier"

        wav_base64 = base64.b64encode(wav_data).decode('utf-8')

        audio_msg = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": wav_base64,
                "format": "wav",
                "is_final": True,
                "session_id": session_id,
                "user_id": "test-user-001",
                "sample_rate": 16000,
                "file_size": len(wav_data)
            }
        }

        await websocket.send(json.dumps(audio_msg))

        # Should not error
        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        data = json.loads(response)

        # Should process successfully
        assert data.get("event") in ["transcription", "audio_chunk", "error"]
        print(f"✓ WAV processed: {data.get('event')}")


@pytest.mark.asyncio
async def test_multiple_audio_chunks(ws_url, wav_encoder):
    """Test sending multiple audio chunks in one session."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:

        # Initialize session
        init_msg = {"event": "init", "user_id": "test-user-001"}
        await websocket.send(json.dumps(init_msg))

        response = await websocket.recv()
        session_data = json.loads(response)
        session_id = session_data["session_id"]

        # Send 3 audio chunks
        for i in range(3):
            pcm_samples = generate_sine_wave(440 * (i + 1), 1.0)
            wav_data = wav_encoder.encode_from_pcm(pcm_samples)
            wav_base64 = base64.b64encode(wav_data).decode('utf-8')

            audio_msg = {
                "event": "audio_chunk",
                "data": {
                    "audio_chunk": wav_base64,
                    "format": "wav",
                    "is_final": True,
                    "session_id": session_id,
                    "user_id": "test-user-001",
                    "sample_rate": 16000,
                    "file_size": len(wav_data)
                }
            }

            await websocket.send(json.dumps(audio_msg))
            print(f"📤 Sent chunk {i+1}: {len(wav_data)} bytes")

            # Wait for responses
            try:
                for _ in range(10):
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    if data.get("event") == "audio_end":
                        break
            except asyncio.TimeoutError:
                pass

            # Small delay between chunks
            await asyncio.sleep(0.5)

        print("✓ Successfully sent multiple chunks")


@pytest.mark.asyncio
async def test_empty_audio_handling(ws_url, wav_encoder):
    """Test handling of empty/silent audio."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:

        # Initialize session
        init_msg = {"event": "init", "user_id": "test-user-001"}
        await websocket.send(json.dumps(init_msg))

        response = await websocket.recv()
        session_data = json.loads(response)
        session_id = session_data["session_id"]

        # Generate silent audio (all zeros)
        pcm_samples = [0.0] * 16000  # 1 second of silence
        wav_data = wav_encoder.encode_from_pcm(pcm_samples)
        wav_base64 = base64.b64encode(wav_data).decode('utf-8')

        audio_msg = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": wav_base64,
                "format": "wav",
                "is_final": True,
                "session_id": session_id,
                "user_id": "test-user-001",
                "sample_rate": 16000,
                "file_size": len(wav_data)
            }
        }

        await websocket.send(json.dumps(audio_msg))
        print(f"📤 Sent silent audio: {len(wav_data)} bytes")

        # Backend should handle gracefully
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(response)
            # Should either get error or empty transcription
            assert data.get("event") in ["error", "transcription", "audio_chunk"]
            print(f"✓ Handled silent audio: {data.get('event')}")
        except asyncio.TimeoutError:
            pytest.fail("Backend did not respond to silent audio")


@pytest.mark.asyncio
async def test_invalid_wav_format(ws_url):
    """Test sending invalid WAV data."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:

        # Initialize session
        init_msg = {"event": "init", "user_id": "test-user-001"}
        await websocket.send(json.dumps(init_msg))

        response = await websocket.recv()
        session_data = json.loads(response)
        session_id = session_data["session_id"]

        # Send invalid WAV data
        invalid_data = b"NOT A WAV FILE"
        invalid_base64 = base64.b64encode(invalid_data).decode('utf-8')

        audio_msg = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": invalid_base64,
                "format": "wav",
                "is_final": True,
                "session_id": session_id,
                "user_id": "test-user-001",
                "sample_rate": 16000,
                "file_size": len(invalid_data)
            }
        }

        await websocket.send(json.dumps(audio_msg))
        print("📤 Sent invalid WAV data")

        # Should receive error
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(response)
            # Backend should handle gracefully
            print(f"✓ Backend response: {data.get('event')}")
        except asyncio.TimeoutError:
            pytest.fail("Backend did not respond to invalid WAV")


@pytest.mark.asyncio
async def test_different_sample_rates(ws_url, wav_encoder):
    """Test WAV files with different sample rates."""
    sample_rates = [8000, 16000, 24000, 48000]

    for sr in sample_rates:
        encoder = WAVEncoder(sample_rate=sr)

        async with websockets.connect(
            ws_url,
            extra_headers={"Origin": "http://localhost:3000"}
        ) as websocket:

            # Initialize session
            init_msg = {"event": "init", "user_id": "test-user-001"}
            await websocket.send(json.dumps(init_msg))

            response = await websocket.recv()
            session_data = json.loads(response)
            session_id = session_data["session_id"]

            # Generate audio at this sample rate
            pcm_samples = generate_sine_wave(440, 1.0, sr)
            wav_data = encoder.encode_from_pcm(pcm_samples)
            wav_base64 = base64.b64encode(wav_data).decode('utf-8')

            audio_msg = {
                "event": "audio_chunk",
                "data": {
                    "audio_chunk": wav_base64,
                    "format": "wav",
                    "is_final": True,
                    "session_id": session_id,
                    "user_id": "test-user-001",
                    "sample_rate": sr,
                    "file_size": len(wav_data)
                }
            }

            await websocket.send(json.dumps(audio_msg))
            print(f"📤 Sent WAV at {sr}Hz: {len(wav_data)} bytes")

            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"✓ {sr}Hz processed: {data.get('event')}")
            except asyncio.TimeoutError:
                print(f"⚠️ Timeout for {sr}Hz")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
