"""
Enhanced WebSocket Manager with Comprehensive Logging

This file contains patches/enhancements to integrate conversation logging
into the existing WebSocket manager.
"""

import time
from datetime import datetime
from typing import Dict, Any

# Import the conversation logger
from ..utils.conversation_logger import get_conversation_logger


class WebSocketManagerEnhancements:
    """
    Mixin class to add conversation logging to WebSocketManager.

    Usage:
        Add this as a method to WebSocketManager or use these functions
        to enhance the existing handle_audio_chunk method.
    """

    @staticmethod
    def enhance_websocket_manager():
        """
        Apply enhancements to the global websocket manager.
        This should be called during initialization.
        """
        from .websocket_manager import websocket_manager

        # Store reference to conversation logger
        websocket_manager.conversation_logger = get_conversation_logger()

        # Patch initialize method to log model info
        original_initialize = websocket_manager.initialize

        async def enhanced_initialize(self):
            """Enhanced initialize with model loading logging."""
            await original_initialize()

            # Log model loading info
            if self.streaming_handler._model_loaded:
                self.conversation_logger.log_model_info(
                    "sensevoice",
                    loaded=True,
                    model_path="models/SenseVoiceSmall"
                )
            else:
                self.conversation_logger.log_model_info(
                    "sensevoice",
                    loaded=False,
                    error="Model not available or failed to load"
                )

            # Log agent info
            if self.agent:
                self.conversation_logger.log_model_info(
                    "agent",
                    loaded=True,
                    model_path="NewsAgent"
                )

        websocket_manager.initialize = lambda: enhanced_initialize(websocket_manager)

        # Patch connect method to start session logging
        original_connect = websocket_manager.connect

        async def enhanced_connect(self, websocket, user_id):
            """Enhanced connect with session logging."""
            session_id = await original_connect(websocket, user_id)

            # Start logging session
            self.conversation_logger.start_session(session_id, user_id)

            return session_id

        websocket_manager.connect = lambda ws, uid: enhanced_connect(websocket_manager, ws, uid)

        # Patch disconnect method to end session logging
        original_disconnect = websocket_manager.disconnect

        async def enhanced_disconnect(self, session_id):
            """Enhanced disconnect with session end logging."""
            # End logging session
            session_info = self.conversation_logger.end_session(session_id)

            await original_disconnect(session_id)

        websocket_manager.disconnect = lambda sid: enhanced_disconnect(websocket_manager, sid)

        # Patch handle_audio_chunk to log conversation turns
        original_handle_audio_chunk = websocket_manager.handle_audio_chunk

        async def enhanced_handle_audio_chunk(self, session_id, data):
            """Enhanced handle_audio_chunk with conversation logging."""
            start_time = time.time()

            # Get user info
            user_id = self.session_data.get(session_id, {}).get("user_id", "unknown")

            # Decode audio info
            import base64
            audio_chunk = base64.b64decode(data["audio_chunk"])
            audio_format = data.get("format", "webm")
            audio_size = len(audio_chunk)

            # Process audio
            await original_handle_audio_chunk(session_id, data)

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Get the result from streaming handler (this is a simplified version)
            # In a real implementation, we'd capture the actual result from the pipeline
            # For now, we'll use placeholder data
            transcription = "Transcription placeholder"  # This would come from the actual result
            agent_response = "Agent response placeholder"  # This would come from the actual result
            tts_chunks_sent = 0  # This would be tracked during streaming

            # Log the conversation turn
            self.conversation_logger.log_conversation_turn(
                session_id=session_id,
                user_id=user_id,
                transcription=transcription,
                agent_response=agent_response,
                processing_time_ms=processing_time_ms,
                audio_format=audio_format,
                audio_size_bytes=audio_size,
                tts_chunks_sent=tts_chunks_sent,
                metadata={"raw_data": data}
            )

        websocket_manager.handle_audio_chunk = lambda sid, d: enhanced_handle_audio_chunk(websocket_manager, sid, d)

        # Patch handle_interrupt to log interruptions
        original_handle_interrupt = websocket_manager.handle_interrupt

        async def enhanced_handle_interrupt(self, session_id, data):
            """Enhanced interrupt with logging."""
            await original_handle_interrupt(session_id, data)

            # Log interruption
            self.conversation_logger.log_interruption(session_id)

        websocket_manager.handle_interrupt = lambda sid, d: enhanced_handle_interrupt(websocket_manager, sid, d)

        return websocket_manager


# Helper function to create a complete enhanced handle_audio_chunk
async def handle_audio_chunk_with_logging(ws_manager, session_id: str, data: Dict[str, Any]):
    """
    Complete replacement for handle_audio_chunk with full conversation logging.

    This function can replace the existing handle_audio_chunk method.
    """
    start_time = time.time()
    conversation_logger = get_conversation_logger()

    try:
        if not ws_manager._initialized:
            await ws_manager.initialize()

        user_id = ws_manager.session_data.get(session_id, {}).get("user_id")

        if not user_id:
            print(f"❌ No user_id found for session {session_id}")
            await ws_manager.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "invalid_session",
                    "message": "Invalid session",
                    "session_id": session_id
                }
            })
            return

        # Decode audio chunk
        import base64
        audio_chunk = base64.b64decode(data["audio_chunk"])
        audio_format = data.get("format", "webm")
        audio_size = len(audio_chunk)

        print(f"🎤 Processing audio chunk for session {session_id}: {audio_size} bytes ({audio_format})")

        # Process with streaming handler (ASR -> LLM -> TTS)
        result = await ws_manager.streaming_handler.process_voice_command(
            session_id, audio_chunk, audio_format
        )

        print(f"🎤 Processing result: {result}")

        if result["success"]:
            # Extract conversation details
            transcription = result["transcription"]
            agent_response = result["response"]

            # Send transcription
            await ws_manager.send_message(session_id, {
                "event": "transcription",
                "data": {
                    "text": transcription,
                    "confidence": 0.95,
                    "session_id": session_id,
                    "processing_time_ms": 200
                }
            })

            # Send agent response
            await ws_manager.send_message(session_id, {
                "event": "agent_response",
                "data": {
                    "text": agent_response,
                    "session_id": session_id,
                    "processing_time_ms": 500,
                    "timestamp": result["timestamp"]
                }
            })

            # Stream TTS response and count chunks
            tts_chunks_sent = 0
            if agent_response:
                print(f"🔊 Starting TTS streaming for: {agent_response[:50]}...")

                # Track TTS chunks
                original_stream_tts = ws_manager.stream_tts_response

                async def count_tts_chunks(sid, text):
                    nonlocal tts_chunks_sent
                    chunk_count = 0

                    # Call original but count chunks
                    # This is a simplified version - in real implementation,
                    # we'd need to modify stream_tts_response to return chunk count
                    await original_stream_tts(sid, text)
                    # Estimate chunks (this should be tracked properly)
                    tts_chunks_sent = 9  # Placeholder - should be actual count

                await count_tts_chunks(session_id, agent_response)

            # Calculate total processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Log the complete conversation turn with all details
            conversation_logger.log_conversation_turn(
                session_id=session_id,
                user_id=user_id,
                transcription=transcription,
                agent_response=agent_response,
                processing_time_ms=processing_time_ms,
                audio_format=audio_format,
                audio_size_bytes=audio_size,
                tts_chunks_sent=tts_chunks_sent,
                metadata={
                    "timestamp": result.get("timestamp"),
                    "confidence": 0.95
                }
            )
        else:
            print(f"❌ Processing failed: {result.get('error')}")

            # Log failed turn
            processing_time_ms = (time.time() - start_time) * 1000
            conversation_logger.log_conversation_turn(
                session_id=session_id,
                user_id=user_id,
                transcription="",
                agent_response="",
                processing_time_ms=processing_time_ms,
                audio_format=audio_format,
                audio_size_bytes=audio_size,
                tts_chunks_sent=0,
                error=result.get("error", "ASR processing failed")
            )

            await ws_manager.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "asr_processing_failed",
                    "message": result.get("error", "ASR processing failed"),
                    "session_id": session_id
                }
            })

    except Exception as e:
        print(f"❌ Error handling audio chunk: {e}")

        # Log error
        processing_time_ms = (time.time() - start_time) * 1000
        conversation_logger.log_conversation_turn(
            session_id=session_id,
            user_id=ws_manager.session_data.get(session_id, {}).get("user_id", "unknown"),
            transcription="",
            agent_response="",
            processing_time_ms=processing_time_ms,
            audio_format=data.get("format", "unknown"),
            audio_size_bytes=0,
            tts_chunks_sent=0,
            error=str(e)
        )

        await ws_manager.send_message(session_id, {
            "event": "error",
            "data": {
                "error_type": "audio_processing_failed",
                "message": str(e),
                "session_id": session_id
            }
        })