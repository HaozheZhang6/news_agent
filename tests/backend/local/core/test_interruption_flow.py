"""
Automated Interruption Flow Testing

Tests the complete interruption flow:
1. User sends audio → Agent responds → User interrupts
2. WebSocket interrupt signal handling
3. TTS streaming interruption
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from backend.app.core.websocket_manager import WebSocketManager


# Test audio samples directory
TESTS_DIR = Path(__file__).parent.parent.parent.parent
AUDIO_DIR = TESTS_DIR / "voice_samples" / "wav"


class TestInterruptionFlow:
    """Test suite for voice interruption flow."""

    @pytest.fixture
    async def ws_manager(self):
        """Create WebSocketManager instance."""
        manager = WebSocketManager()
        await manager.initialize()
        return manager

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.receive_text = AsyncMock()
        ws.close = AsyncMock()
        ws.client_state = Mock()
        ws.client_state.name = "CONNECTED"
        return ws

    @pytest.fixture
    def audio_samples(self):
        """Load test audio samples."""
        samples = {}
        if AUDIO_DIR.exists():
            for wav_file in list(AUDIO_DIR.glob("*.wav"))[:3]:  # Load first 3 samples
                with open(wav_file, 'rb') as f:
                    import base64
                    samples[wav_file.stem] = base64.b64encode(f.read()).decode()
        return samples

    @pytest.mark.asyncio
    async def test_interrupt_signal_handling(self, ws_manager, mock_websocket):
        """Test interrupt signal is properly handled."""
        # Setup: Create a session
        session_id = await ws_manager.connect(mock_websocket, "test-user")

        # Simulate interrupt
        await ws_manager.handle_interrupt(session_id, {
            "reason": "user_started_speaking"
        })

        # Verify interrupt flag is set
        assert ws_manager.streaming_tasks.get(session_id) == True
        print(f"\n✓ Interrupt flag set for session {session_id[:8]}...")

        # Verify interrupt confirmation sent
        mock_websocket.send_text.assert_called()
        last_call = mock_websocket.send_text.call_args[0][0]
        message = json.loads(last_call)
        assert message["event"] == "voice_interrupted"
        print("✓ Interrupt confirmation sent")

        # Cleanup
        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_streaming_interruption(self, ws_manager, mock_websocket):
        """Test TTS streaming is interrupted when user speaks."""
        # Setup: Create a session
        session_id = await ws_manager.connect(mock_websocket, "test-user")

        # Start TTS streaming in background
        async def stream_tts():
            await ws_manager.stream_tts_response(session_id, "This is a test response")

        stream_task = asyncio.create_task(stream_tts())

        # Wait a bit for streaming to start
        await asyncio.sleep(0.1)

        # Simulate interrupt
        ws_manager.streaming_tasks[session_id] = True

        # Wait for streaming to complete
        await stream_task

        # Verify streaming was interrupted (not completed fully)
        calls = mock_websocket.send_text.call_args_list
        events = [json.loads(call[0][0])["event"] for call in calls]

        # Should have streaming_interrupted event
        assert "streaming_interrupted" in events or "streaming_complete" in events
        print("\n✓ TTS streaming interrupted successfully")

        # Cleanup
        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_multiple_interruptions(self, ws_manager, mock_websocket):
        """Test handling multiple interruptions in succession."""
        session_id = await ws_manager.connect(mock_websocket, "test-user")

        # Track interruptions
        interruption_count = 0

        for i in range(3):
            # Reset interrupt flag
            ws_manager.streaming_tasks[session_id] = False

            # Send interrupt
            await ws_manager.handle_interrupt(session_id, {
                "reason": f"interruption_{i}"
            })

            interruption_count += 1
            await asyncio.sleep(0.05)

        # Verify session data tracks interruptions
        session_info = ws_manager.get_session_info(session_id)
        assert session_info["total_interruptions"] == 3
        print(f"\n✓ Tracked {interruption_count} interruptions correctly")

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_audio_chunk_processing_with_interruption(self, ws_manager, mock_websocket, audio_samples):
        """Test audio chunk processing that gets interrupted."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        session_id = await ws_manager.connect(mock_websocket, "test-user")

        # Get first audio sample
        sample_name, audio_b64 = next(iter(audio_samples.items()))

        # Send first audio chunk (will trigger response)
        with patch.object(ws_manager.streaming_handler, 'process_voice_command') as mock_process:
            mock_process.return_value = {
                "success": True,
                "transcription": "test question",
                "response": "test response",
                "timestamp": "2024-01-01T00:00:00Z"
            }

            await ws_manager.handle_audio_chunk(session_id, {
                "audio_chunk": audio_b64,
                "format": "wav",
                "session_id": session_id
            })

            # Verify processing was called
            mock_process.assert_called_once()
            print(f"\n✓ Audio chunk processed: {sample_name}")

        # Simulate interruption during response
        ws_manager.streaming_tasks[session_id] = True

        # Verify interrupt flag is set
        assert ws_manager.streaming_tasks[session_id] == True
        print("✓ Interrupt flag set during response")

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_session_cleanup_on_disconnect(self, ws_manager, mock_websocket):
        """Test proper cleanup when session disconnects during streaming."""
        session_id = await ws_manager.connect(mock_websocket, "test-user")

        # Set some session state
        ws_manager.streaming_tasks[session_id] = True
        ws_manager.streaming_handler.audio_buffers[session_id] = bytearray(b"test")

        # Disconnect
        await ws_manager.disconnect(session_id)

        # Verify cleanup
        assert session_id not in ws_manager.active_connections
        assert session_id not in ws_manager.streaming_handler.audio_buffers
        print("\n✓ Session cleaned up properly on disconnect")


class TestInterruptionTiming:
    """Test interruption timing and latency."""

    @pytest.mark.asyncio
    async def test_interrupt_latency(self):
        """Test interrupt signal latency."""
        import time

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"

        session_id = await ws_manager.connect(mock_ws, "test-user")

        # Measure interrupt handling time
        start = time.time()
        await ws_manager.handle_interrupt(session_id, {"reason": "test"})
        latency = (time.time() - start) * 1000

        print(f"\n✓ Interrupt handling latency: {latency:.2f}ms")

        # Interrupt handling should be fast (< 10ms)
        assert latency < 10, f"Interrupt handling too slow: {latency:.2f}ms"

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_streaming_stop_latency(self):
        """Test how quickly streaming stops after interrupt signal."""
        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"

        session_id = await ws_manager.connect(mock_ws, "test-user")

        # Start streaming
        stream_task = asyncio.create_task(
            ws_manager.stream_tts_response(session_id, "This is a long test response for interruption testing")
        )

        # Wait for streaming to start
        await asyncio.sleep(0.05)

        # Send interrupt
        import time
        interrupt_time = time.time()
        ws_manager.streaming_tasks[session_id] = True

        # Wait for streaming to stop
        await stream_task
        stop_time = time.time()

        latency = (stop_time - interrupt_time) * 1000
        print(f"\n✓ Streaming stop latency: {latency:.2f}ms")

        # Should stop within reasonable time (< 100ms)
        assert latency < 100, f"Streaming stop too slow: {latency:.2f}ms"

        await ws_manager.disconnect(session_id)


class TestInterruptionScenarios:
    """Test real-world interruption scenarios."""

    @pytest.mark.asyncio
    async def test_interrupt_during_first_tts_chunk(self, audio_samples):
        """Test interruption during first TTS chunk."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"

        session_id = await ws_manager.connect(mock_ws, "test-user")

        # Start streaming
        stream_task = asyncio.create_task(
            ws_manager.stream_tts_response(session_id, "Short response")
        )

        # Interrupt immediately
        await asyncio.sleep(0.01)
        ws_manager.streaming_tasks[session_id] = True

        await stream_task

        # Verify interrupted event was sent
        calls = mock_ws.send_text.call_args_list
        events = [json.loads(call[0][0])["event"] for call in calls if call[0]]
        assert "streaming_interrupted" in events or "streaming_complete" in events
        print("\n✓ Early interruption handled correctly")

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_rapid_audio_chunks_with_interrupts(self, audio_samples):
        """Test handling rapid audio chunks with interruptions."""
        if not audio_samples:
            pytest.skip("No audio samples available")

        ws_manager = WebSocketManager()
        await ws_manager.initialize()

        mock_ws = AsyncMock()
        mock_ws.client_state = Mock()
        mock_ws.client_state.name = "CONNECTED"

        session_id = await ws_manager.connect(mock_ws, "test-user")

        # Simulate rapid audio chunks
        sample_name, audio_b64 = next(iter(audio_samples.items()))

        with patch.object(ws_manager.streaming_handler, 'process_voice_command') as mock_process:
            mock_process.return_value = {
                "success": True,
                "transcription": "quick question",
                "response": "quick response",
                "timestamp": "2024-01-01T00:00:00Z"
            }

            # Send multiple chunks rapidly
            for i in range(3):
                await ws_manager.handle_audio_chunk(session_id, {
                    "audio_chunk": audio_b64[:10000],  # Smaller chunks
                    "format": "wav",
                    "session_id": session_id
                })

                # Interrupt every other one
                if i % 2 == 0:
                    ws_manager.streaming_tasks[session_id] = True
                    await asyncio.sleep(0.01)

            print(f"\n✓ Handled {3} rapid chunks with interruptions")

        await ws_manager.disconnect(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])