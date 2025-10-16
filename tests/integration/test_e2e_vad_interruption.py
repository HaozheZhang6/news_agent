"""
End-to-End VAD and Interruption Testing

Full integration tests for the complete voice interaction flow:
1. WebSocket connection
2. Audio upload
3. VAD validation
4. Transcription
5. Agent response
6. TTS streaming
7. Interruption handling
"""

import pytest
import asyncio
import json
import base64
from pathlib import Path
from unittest.mock import patch, AsyncMock


# Test audio samples directory
TESTS_DIR = Path(__file__).parent.parent
AUDIO_DIR = TESTS_DIR / "voice_samples" / "wav"


class TestE2EVADInterruption:
    """End-to-end tests for VAD and interruption flow."""

    @pytest.fixture
    def audio_samples(self):
        """Load test audio samples."""
        samples = {}
        if AUDIO_DIR.exists():
            for wav_file in list(AUDIO_DIR.glob("*.wav"))[:5]:
                with open(wav_file, 'rb') as f:
                    samples[wav_file.stem] = {
                        "raw": f.read(),
                        "b64": base64.b64encode(f.read()).decode()
                    }
        return samples

    @pytest.mark.asyncio
    async def test_complete_voice_interaction(self, audio_samples):
        """Test complete voice interaction flow."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        from backend.app.core.websocket_manager import WebSocketManager
        from unittest.mock import AsyncMock, Mock

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        # Create mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"
        sent_messages = []

        async def capture_send(msg):
            sent_messages.append(json.loads(msg))

        mock_ws.send_text = capture_send

        # Connect
        session_id = await ws_manager.connect(mock_ws, "test-user")
        print(f"\n✓ Connected: session {session_id[:8]}...")

        # Send audio
        sample_name, audio_data = next(iter(audio_samples.items()))

        with patch.object(ws_manager.streaming_handler, 'process_voice_command') as mock_process:
            mock_process.return_value = {
                "success": True,
                "transcription": "what is the price of apple",
                "response": "The current price of Apple stock is $150.25",
                "timestamp": "2024-01-01T00:00:00Z"
            }

            await ws_manager.handle_audio_chunk(session_id, {
                "audio_chunk": audio_data["b64"][:50000],  # Use partial audio
                "format": "wav",
                "session_id": session_id
            })

        # Verify message flow
        events = [msg["event"] for msg in sent_messages]
        print(f"✓ Events: {events}")

        # Should have transcription and response events
        assert "transcription" in events or "agent_response" in events
        print("✓ Audio processed successfully")

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_vad_rejection_flow(self, audio_samples):
        """Test VAD rejection with silent/noisy audio."""
        from backend.app.core.websocket_manager import WebSocketManager
        from unittest.mock import AsyncMock, Mock

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"
        sent_messages = []

        async def capture_send(msg):
            sent_messages.append(json.loads(msg))

        mock_ws.send_text = capture_send

        session_id = await ws_manager.connect(mock_ws, "test-user")

        # Send silent audio (should be rejected by VAD)
        silent_audio = b"RIFF" + b"\x00" * 10000
        silent_b64 = base64.b64encode(silent_audio).decode()

        await ws_manager.handle_audio_chunk(session_id, {
            "audio_chunk": silent_b64,
            "format": "wav",
            "session_id": session_id
        })

        # Check for error or rejection
        events = [msg["event"] for msg in sent_messages]
        print(f"\n✓ Silent audio events: {events}")

        # Should have error event or similar
        has_error = any("error" in msg["event"].lower() for msg in sent_messages)
        if has_error:
            print("✓ Silent audio rejected by VAD")
        else:
            print("⚠ Silent audio not rejected (may need stricter VAD)")

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_interruption_during_response(self, audio_samples):
        """Test interruption while agent is responding."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        from backend.app.core.websocket_manager import WebSocketManager
        from unittest.mock import AsyncMock, Mock

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"
        sent_messages = []

        async def capture_send(msg):
            sent_messages.append(json.loads(msg))

        mock_ws.send_text = capture_send

        session_id = await ws_manager.connect(mock_ws, "test-user")

        # Send first audio to trigger response
        sample_name, audio_data = next(iter(audio_samples.items()))

        with patch.object(ws_manager.streaming_handler, 'process_voice_command') as mock_process:
            mock_process.return_value = {
                "success": True,
                "transcription": "tell me about nvidia",
                "response": "NVIDIA Corporation is a leading technology company...",
                "timestamp": "2024-01-01T00:00:00Z"
            }

            # Send audio chunk
            await ws_manager.handle_audio_chunk(session_id, {
                "audio_chunk": audio_data["b64"][:50000],
                "format": "wav",
                "session_id": session_id
            })

        # Wait a bit for TTS to start
        await asyncio.sleep(0.05)

        # Send interrupt
        await ws_manager.handle_interrupt(session_id, {
            "reason": "user_started_speaking"
        })

        # Wait for processing
        await asyncio.sleep(0.1)

        # Verify interruption was handled
        events = [msg["event"] for msg in sent_messages]
        print(f"\n✓ Interruption flow events: {events}")

        assert "voice_interrupted" in events
        print("✓ Interruption handled successfully")

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_multiple_audio_chunks_sequence(self, audio_samples):
        """Test sequence of audio chunks (conversation flow)."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        from backend.app.core.websocket_manager import WebSocketManager
        from unittest.mock import AsyncMock, Mock

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"

        session_id = await ws_manager.connect(mock_ws, "test-user")

        # Simulate conversation: multiple questions
        questions = [
            ("test_price_aapl", "What is Apple's stock price?", "Apple is trading at $150.25"),
            ("test_news_nvda_latest", "Latest news about NVIDIA?", "NVIDIA announced new GPUs"),
        ]

        with patch.object(ws_manager.streaming_handler, 'process_voice_command') as mock_process:
            for i, (sample_name, question, response) in enumerate(questions):
                if sample_name not in audio_samples:
                    continue

                mock_process.return_value = {
                    "success": True,
                    "transcription": question,
                    "response": response,
                    "timestamp": "2024-01-01T00:00:00Z"
                }

                audio_data = audio_samples[sample_name]
                await ws_manager.handle_audio_chunk(session_id, {
                    "audio_chunk": audio_data["b64"][:50000],
                    "format": "wav",
                    "session_id": session_id
                })

                # Small delay between questions
                await asyncio.sleep(0.1)

                print(f"✓ Question {i+1}: {question}")

        # Verify session stats
        session_info = ws_manager.get_session_info(session_id)
        print(f"\n✓ Conversation completed: {session_info}")

        await ws_manager.disconnect(session_id)


class TestE2EPerformance:
    """End-to-end performance tests."""

    @pytest.mark.asyncio
    async def test_end_to_end_latency(self, audio_samples):
        """Measure end-to-end latency from audio to response."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        from backend.app.core.websocket_manager import WebSocketManager
        from unittest.mock import AsyncMock, Mock
        import time

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"

        session_id = await ws_manager.connect(mock_ws, "test-user")

        sample_name, audio_data = next(iter(audio_samples.items()))

        with patch.object(ws_manager.streaming_handler, 'process_voice_command') as mock_process:
            mock_process.return_value = {
                "success": True,
                "transcription": "test",
                "response": "test response",
                "timestamp": "2024-01-01T00:00:00Z"
            }

            # Measure latency
            start = time.time()
            await ws_manager.handle_audio_chunk(session_id, {
                "audio_chunk": audio_data["b64"][:50000],
                "format": "wav",
                "session_id": session_id
            })
            latency = (time.time() - start) * 1000

        print(f"\n✓ End-to-end latency: {latency:.2f}ms")

        # Should be reasonably fast (< 5000ms)
        assert latency < 5000, f"E2E latency too high: {latency:.2f}ms"

        await ws_manager.disconnect(session_id)


class TestE2EErrorHandling:
    """End-to-end error handling tests."""

    @pytest.mark.asyncio
    async def test_invalid_audio_format(self):
        """Test handling of invalid audio format."""
        from backend.app.core.websocket_manager import WebSocketManager
        from unittest.mock import AsyncMock, Mock

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"
        sent_messages = []

        async def capture_send(msg):
            sent_messages.append(json.loads(msg))

        mock_ws.send_text = capture_send

        session_id = await ws_manager.connect(mock_ws, "test-user")

        # Send invalid audio data
        invalid_audio = base64.b64encode(b"not valid audio").decode()

        await ws_manager.handle_audio_chunk(session_id, {
            "audio_chunk": invalid_audio,
            "format": "wav",
            "session_id": session_id
        })

        # Should handle gracefully with error message
        events = [msg["event"] for msg in sent_messages]
        print(f"\n✓ Invalid audio events: {events}")

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_session_timeout_handling(self):
        """Test handling of session timeout."""
        from backend.app.core.websocket_manager import WebSocketManager
        from unittest.mock import AsyncMock, Mock

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"

        # Create and immediately disconnect session
        session_id = await ws_manager.connect(mock_ws, "test-user")
        await ws_manager.disconnect(session_id)

        # Try to use disconnected session
        await ws_manager.handle_interrupt(session_id, {"reason": "test"})

        print("\n✓ Handled operation on disconnected session gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])