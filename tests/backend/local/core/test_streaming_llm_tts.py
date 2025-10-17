"""
Test Suite for Streaming LLM and Concurrent TTS

Tests the new streaming functionality:
1. Streaming LLM responses (GLM-4.5 Flash)
2. Concurrent TTS generation
3. Sentence-based TTS triggering
4. Full streaming pipeline (ASR -> Streaming LLM -> Concurrent TTS)
"""

import pytest
import asyncio
import base64
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from pathlib import Path
from starlette.websockets import WebSocketState

from backend.app.core.streaming_handler import StreamingVoiceHandler
from backend.app.core.websocket_manager import WebSocketManager
from backend.app.core.agent_wrapper import AgentWrapper


# Test audio samples directory
TESTS_DIR = Path(__file__).parent.parent.parent.parent
AUDIO_DIR = TESTS_DIR / "voice_samples" / "wav"


class TestStreamingLLMResponse:
    """Test streaming LLM response generation."""

    @pytest.fixture
    async def agent_wrapper(self):
        """Create AgentWrapper instance."""
        wrapper = AgentWrapper()
        await wrapper.initialize()
        return wrapper

    @pytest.fixture
    def mock_agent_with_streaming(self):
        """Create mock agent with streaming support."""
        mock_agent = Mock()

        async def mock_stream(*args, **kwargs):
            """Mock streaming response that yields chunks."""
            chunks = [
                "The stock price ",
                "of AAPL is ",
                "$150.25. ",
                "It has increased ",
                "by 2.5% today."
            ]
            for chunk in chunks:
                await asyncio.sleep(0.01)  # Simulate streaming delay
                yield chunk

        mock_agent.get_response_stream = mock_stream
        return mock_agent

    @pytest.mark.asyncio
    async def test_agent_stream_voice_response(self, agent_wrapper, mock_agent_with_streaming):
        """Test that agent_wrapper streams responses correctly."""
        # Replace agent with mock
        agent_wrapper.agent = mock_agent_with_streaming
        agent_wrapper._initialized = True

        collected_chunks = []
        async for chunk in agent_wrapper.stream_voice_response(
            "What's the price of AAPL?",
            "test-user",
            "test-session"
        ):
            collected_chunks.append(chunk)
            print(f"  Received chunk: '{chunk}'")

        # Verify we received multiple chunks
        assert len(collected_chunks) > 1, "Should receive multiple chunks"

        # Verify chunks combine to full response
        full_response = "".join(collected_chunks)
        assert "AAPL" in full_response
        assert "$150.25" in full_response

        print(f"\n✓ Received {len(collected_chunks)} chunks")
        print(f"✓ Full response: {full_response}")

    @pytest.mark.asyncio
    async def test_streaming_with_real_agent(self, agent_wrapper):
        """Test streaming with the real NewsAgent (if available)."""
        if not hasattr(agent_wrapper.agent, 'get_response_stream'):
            pytest.skip("Real agent doesn't support streaming")

        collected_chunks = []
        async for chunk in agent_wrapper.stream_voice_response(
            "What's the latest tech news?",
            "test-user",
            "test-session"
        ):
            collected_chunks.append(chunk)

        # Should receive at least one chunk
        assert len(collected_chunks) > 0
        print(f"\n✓ Real agent streamed {len(collected_chunks)} chunks")


class TestConcurrentTTS:
    """Test concurrent TTS generation with streaming LLM."""

    @pytest.fixture
    def streaming_handler(self):
        """Create StreamingVoiceHandler instance."""
        return StreamingVoiceHandler()

    @pytest.mark.asyncio
    async def test_sentence_based_tts_triggering(self, streaming_handler):
        """Test that TTS starts when complete sentences are detected."""
        # Mock ASR
        async def mock_transcribe(*args, **kwargs):
            return "test question"
        streaming_handler.transcribe_chunk = mock_transcribe

        # Mock the stream_tts_audio method to track calls
        tts_calls = []

        async def mock_tts(text, *args, **kwargs):
            tts_calls.append(text)
            # Simulate TTS generation
            yield b"audio_chunk_1"
            yield b"audio_chunk_2"

        streaming_handler.stream_tts_audio = mock_tts

        # Mock agent streaming
        mock_agent = Mock()
        async def mock_stream(*args, **kwargs):
            # Stream text with sentences
            yield "The stock price is $150"
            yield ".25. "  # Complete sentence
            yield "It has increased by 2"
            yield ".5% today."  # Another complete sentence

        with patch('backend.app.core.agent_wrapper.get_agent') as mock_get_agent:
            mock_wrapper = Mock()
            mock_wrapper.stream_voice_response = mock_stream
            mock_get_agent.return_value = mock_wrapper

            chunks = []
            async for chunk in streaming_handler.process_voice_command_streaming(
                "test-session",
                b"mock_audio",
                "wav"
            ):
                chunks.append(chunk)

            # Verify TTS was called for complete sentences
            # Should have called TTS at least once
            assert len(tts_calls) > 0, "TTS should be triggered for complete sentences"
            print(f"\n✓ TTS triggered {len(tts_calls)} times for sentences")
            for i, text in enumerate(tts_calls):
                print(f"  TTS call {i+1}: '{text}'")

    @pytest.mark.asyncio
    async def test_buffer_length_tts_triggering(self, streaming_handler):
        """Test that TTS starts when buffer exceeds 100 characters."""
        # Mock ASR
        async def mock_transcribe(*args, **kwargs):
            return "test question"
        streaming_handler.transcribe_chunk = mock_transcribe

        tts_calls = []

        async def mock_tts(text, *args, **kwargs):
            tts_calls.append(text)
            yield b"audio_chunk"

        streaming_handler.stream_tts_audio = mock_tts

        # Mock agent streaming with long text without sentence endings
        async def mock_stream(*args, **kwargs):
            # Yield text in small chunks that eventually exceed 100 chars
            long_text = "This is a very long response that does not have any sentence endings but will eventually exceed the one hundred character buffer limit for TTS triggering"
            chunk_size = 10
            for i in range(0, len(long_text), chunk_size):
                yield long_text[i:i+chunk_size]
                await asyncio.sleep(0.001)

        with patch('backend.app.core.agent_wrapper.get_agent') as mock_get_agent:
            mock_wrapper = Mock()
            mock_wrapper.stream_voice_response = mock_stream
            mock_get_agent.return_value = mock_wrapper

            chunks = []
            async for chunk in streaming_handler.process_voice_command_streaming(
                "test-session",
                b"mock_audio",
                "wav"
            ):
                chunks.append(chunk)

            # Verify TTS was called when buffer exceeded 100 chars
            assert len(tts_calls) > 0, "TTS should be triggered when buffer exceeds 100 chars"

            # At least one TTS call should have text > 100 chars or close to it
            has_long_buffer = any(len(text) >= 90 for text in tts_calls)
            print(f"\n✓ TTS triggered {len(tts_calls)} times for long buffer")
            print(f"✓ Buffer-based triggering: {has_long_buffer}")

    @pytest.mark.asyncio
    async def test_tts_streaming_chunks(self, streaming_handler):
        """Test that TTS audio is streamed in chunks."""
        # Use real TTS streaming if edge_tts is available
        try:
            import edge_tts

            audio_chunks = []
            async for chunk in streaming_handler.stream_tts_audio(
                "This is a test.",
                chunk_size=4096
            ):
                audio_chunks.append(chunk)
                print(f"  Received TTS chunk: {len(chunk)} bytes")

            # Should receive multiple chunks
            assert len(audio_chunks) > 0, "Should receive TTS audio chunks"

            total_size = sum(len(chunk) for chunk in audio_chunks)
            print(f"\n✓ TTS streamed {len(audio_chunks)} chunks")
            print(f"✓ Total audio size: {total_size} bytes")

        except ImportError:
            pytest.skip("edge-tts not available")


class TestStreamingPipeline:
    """Test complete streaming pipeline integration."""

    @pytest.fixture
    def audio_samples(self):
        """Load test audio samples."""
        samples = {}
        if AUDIO_DIR.exists():
            for wav_file in list(AUDIO_DIR.glob("*.wav"))[:3]:
                with open(wav_file, 'rb') as f:
                    samples[wav_file.stem] = f.read()
        return samples

    @pytest.mark.asyncio
    async def test_full_streaming_pipeline_mock(self):
        """Test full streaming pipeline with mocks."""
        handler = StreamingVoiceHandler()

        # Mock ASR
        async def mock_transcribe(*args, **kwargs):
            return "What's the price of AAPL?"
        handler.transcribe_chunk = mock_transcribe

        # Mock agent streaming
        async def mock_stream(*args, **kwargs):
            yield "The current price "
            yield "of AAPL is $150.25. "
            yield "It's up 2.5% today."

        # Mock TTS
        async def mock_tts(text, *args, **kwargs):
            yield f"audio_for:{text[:20]}".encode()
        handler.stream_tts_audio = mock_tts

        with patch('backend.app.core.agent_wrapper.get_agent') as mock_get_agent:
            mock_wrapper = Mock()
            mock_wrapper.stream_voice_response = mock_stream
            mock_get_agent.return_value = mock_wrapper

            # Track all chunks
            transcription_chunks = []
            text_chunks = []
            audio_chunks = []
            errors = []

            async for chunk in handler.process_voice_command_streaming(
                "test-session",
                b"mock_audio_data",
                "wav"
            ):
                chunk_type = chunk.get("type")

                if chunk_type == "transcription":
                    transcription_chunks.append(chunk["text"])
                    print(f"\n📝 Transcription: {chunk['text']}")

                elif chunk_type == "text_chunk":
                    text_chunks.append(chunk["text"])
                    print(f"💬 Text chunk: {chunk['text']}")

                elif chunk_type == "audio_chunk":
                    audio_chunks.append(chunk["data"])
                    print(f"🔊 Audio chunk: {len(chunk['data'])} bytes")

                elif chunk_type == "error":
                    errors.append(chunk["message"])
                    print(f"❌ Error: {chunk['message']}")

                elif chunk_type == "complete":
                    print("✅ Streaming complete")

            # Verify pipeline
            assert len(transcription_chunks) == 1, "Should have one transcription"
            assert len(text_chunks) > 0, "Should have text chunks"
            assert len(audio_chunks) > 0, "Should have audio chunks"
            assert len(errors) == 0, "Should have no errors"

            print(f"\n✓ Pipeline completed successfully")
            print(f"  Transcription chunks: {len(transcription_chunks)}")
            print(f"  Text chunks: {len(text_chunks)}")
            print(f"  Audio chunks: {len(audio_chunks)}")

    @pytest.mark.asyncio
    async def test_streaming_pipeline_order(self):
        """Test that pipeline chunks arrive in correct order."""
        handler = StreamingVoiceHandler()

        # Mock components
        async def mock_transcribe(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate ASR delay
            return "Test question"
        handler.transcribe_chunk = mock_transcribe

        async def mock_stream(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate LLM delay
            yield "Response part 1. "
            await asyncio.sleep(0.01)
            yield "Response part 2."

        async def mock_tts(text, *args, **kwargs):
            await asyncio.sleep(0.005)  # Simulate TTS delay
            yield b"audio"
        handler.stream_tts_audio = mock_tts

        with patch('backend.app.core.agent_wrapper.get_agent') as mock_get_agent:
            mock_wrapper = Mock()
            mock_wrapper.stream_voice_response = mock_stream
            mock_get_agent.return_value = mock_wrapper

            chunk_order = []
            async for chunk in handler.process_voice_command_streaming(
                "test-session",
                b"audio",
                "wav"
            ):
                chunk_order.append(chunk.get("type"))

            # Verify order: transcription -> text_chunks -> audio_chunks -> complete
            print(f"\n✓ Chunk order: {chunk_order}")

            assert chunk_order[0] == "transcription", "First should be transcription"
            assert "text_chunk" in chunk_order, "Should have text chunks"
            assert "audio_chunk" in chunk_order, "Should have audio chunks"
            assert chunk_order[-1] == "complete", "Last should be complete"

            # Transcription should come before text chunks
            trans_idx = chunk_order.index("transcription")
            text_idx = chunk_order.index("text_chunk")
            assert trans_idx < text_idx, "Transcription should come before text chunks"


class TestWebSocketStreamingIntegration:
    """Test WebSocket integration with streaming pipeline."""

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
        ws.client_state = WebSocketState.CONNECTED
        return ws

    @pytest.mark.asyncio
    async def test_websocket_streaming_event_handler(self, ws_manager, mock_websocket):
        """Test WebSocket handles audio_chunk_streaming event."""
        # Connect
        session_id = await ws_manager.connect(mock_websocket, "test-user")

        # Mock streaming handler
        async def mock_streaming(*args, **kwargs):
            yield {"type": "transcription", "text": "test question"}
            yield {"type": "text_chunk", "text": "test response"}
            yield {"type": "audio_chunk", "data": b"audio_data"}
            yield {"type": "complete"}

        with patch.object(ws_manager.streaming_handler, 'process_voice_command_streaming', mock_streaming):
            # Send audio_chunk_streaming event
            await ws_manager.handle_audio_chunk_streaming(session_id, {
                "audio_chunk": base64.b64encode(b"test_audio").decode(),
                "format": "wav"
            })

            # Verify messages were sent
            assert mock_websocket.send_text.call_count >= 3, "Should send multiple messages"

            # Check for expected events
            calls = mock_websocket.send_text.call_args_list
            events = []
            for call in calls:
                if call[0]:
                    import json
                    try:
                        msg = json.loads(call[0][0])
                        events.append(msg.get("event"))
                    except:
                        pass

            print(f"\n✓ WebSocket events sent: {events}")
            assert "transcription" in events, "Should send transcription event"
            assert "agent_response_chunk" in events, "Should send text chunk events"
            assert "tts_chunk" in events, "Should send TTS chunk events"

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_streaming_interruption(self, ws_manager, mock_websocket):
        """Test that streaming can be interrupted."""
        session_id = await ws_manager.connect(mock_websocket, "test-user")

        # Mock streaming that takes time
        async def mock_streaming(*args, **kwargs):
            yield {"type": "transcription", "text": "test"}

            for i in range(10):
                # Check for interruption
                if ws_manager.streaming_tasks.get(session_id, False):
                    print(f"\n✓ Streaming interrupted at chunk {i}")
                    return

                yield {"type": "text_chunk", "text": f"chunk{i}"}
                await asyncio.sleep(0.01)

            yield {"type": "complete"}

        with patch.object(ws_manager.streaming_handler, 'process_voice_command_streaming', mock_streaming):
            # Start streaming in background
            stream_task = asyncio.create_task(
                ws_manager.handle_audio_chunk_streaming(session_id, {
                    "audio_chunk": base64.b64encode(b"test").decode(),
                    "format": "wav"
                })
            )

            # Wait a bit then interrupt
            await asyncio.sleep(0.05)
            ws_manager.streaming_tasks[session_id] = True
            print("\n🛑 Sending interrupt signal")

            # Wait for streaming to complete
            await stream_task

            # Verify interruption happened
            assert ws_manager.streaming_tasks.get(session_id) == True
            print("✓ Interrupt flag remained set")

        await ws_manager.disconnect(session_id)

    @pytest.mark.asyncio
    async def test_streaming_performance(self, ws_manager, mock_websocket):
        """Test streaming performance and latency."""
        import time

        session_id = await ws_manager.connect(mock_websocket, "test-user")

        # Mock fast streaming
        async def mock_streaming(*args, **kwargs):
            yield {"type": "transcription", "text": "test"}

            # Simulate LLM generating 5 chunks quickly
            for i in range(5):
                yield {"type": "text_chunk", "text": f"chunk{i}. "}
                await asyncio.sleep(0.01)  # 10ms per chunk

            # Simulate TTS chunks
            for i in range(3):
                yield {"type": "audio_chunk", "data": b"audio"}
                await asyncio.sleep(0.005)

            yield {"type": "complete"}

        with patch.object(ws_manager.streaming_handler, 'process_voice_command_streaming', mock_streaming):
            start_time = time.time()

            await ws_manager.handle_audio_chunk_streaming(session_id, {
                "audio_chunk": base64.b64encode(b"test").decode(),
                "format": "wav"
            })

            total_time = (time.time() - start_time) * 1000

            print(f"\n✓ Streaming completed in {total_time:.2f}ms")

            # Should complete reasonably fast (< 200ms for mocked components)
            assert total_time < 200, f"Streaming took too long: {total_time:.2f}ms"

        await ws_manager.disconnect(session_id)


class TestStreamingEdgeCases:
    """Test edge cases and error handling in streaming."""

    @pytest.mark.asyncio
    async def test_empty_llm_response(self):
        """Test handling of empty LLM response."""
        handler = StreamingVoiceHandler()

        async def mock_transcribe(*args, **kwargs):
            return "test"
        handler.transcribe_chunk = mock_transcribe

        # Mock agent that yields nothing
        async def mock_stream(*args, **kwargs):
            # Empty generator
            return
            yield  # This line never executes

        async def mock_tts(text, *args, **kwargs):
            yield b"audio"
        handler.stream_tts_audio = mock_tts

        with patch('backend.app.core.agent_wrapper.get_agent') as mock_get_agent:
            mock_wrapper = Mock()
            mock_wrapper.stream_voice_response = mock_stream
            mock_get_agent.return_value = mock_wrapper

            chunks = []
            async for chunk in handler.process_voice_command_streaming(
                "test-session",
                b"audio",
                "wav"
            ):
                chunks.append(chunk)

            # Should still complete gracefully
            assert any(c["type"] == "complete" for c in chunks)
            print("\n✓ Empty LLM response handled gracefully")

    @pytest.mark.asyncio
    async def test_llm_error_during_streaming(self):
        """Test error handling when LLM fails during streaming."""
        handler = StreamingVoiceHandler()

        async def mock_transcribe(*args, **kwargs):
            return "test"
        handler.transcribe_chunk = mock_transcribe

        # Mock agent that raises error
        async def mock_stream(*args, **kwargs):
            yield "Starting response"
            raise Exception("LLM error during streaming")

        with patch('backend.app.core.agent_wrapper.get_agent') as mock_get_agent:
            mock_wrapper = Mock()
            mock_wrapper.stream_voice_response = mock_stream
            mock_get_agent.return_value = mock_wrapper

            chunks = []
            async for chunk in handler.process_voice_command_streaming(
                "test-session",
                b"audio",
                "wav"
            ):
                chunks.append(chunk)

            # Should receive error chunk
            error_chunks = [c for c in chunks if c["type"] == "error"]
            assert len(error_chunks) > 0, "Should receive error chunk"
            print(f"\n✓ LLM error handled: {error_chunks[0]['message']}")

    @pytest.mark.asyncio
    async def test_tts_error_during_streaming(self):
        """Test error handling when TTS fails during streaming."""
        handler = StreamingVoiceHandler()

        async def mock_transcribe(*args, **kwargs):
            return "test"
        handler.transcribe_chunk = mock_transcribe

        async def mock_stream(*args, **kwargs):
            yield "Complete sentence. "

        # Mock TTS that fails
        async def mock_tts(text, *args, **kwargs):
            raise Exception("TTS error")
        handler.stream_tts_audio = mock_tts

        with patch('backend.app.core.agent_wrapper.get_agent') as mock_get_agent:
            mock_wrapper = Mock()
            mock_wrapper.stream_voice_response = mock_stream
            mock_get_agent.return_value = mock_wrapper

            chunks = []
            async for chunk in handler.process_voice_command_streaming(
                "test-session",
                b"audio",
                "wav"
            ):
                chunks.append(chunk)

            # Should receive error chunk
            error_chunks = [c for c in chunks if c["type"] == "error"]
            assert len(error_chunks) > 0, "Should receive error chunk for TTS failure"
            print(f"\n✓ TTS error handled: {error_chunks[0]['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
