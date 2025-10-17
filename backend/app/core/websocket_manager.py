"""WebSocket manager for real-time voice communication."""
import asyncio
import json
import uuid
import logging
import base64
import time
from typing import Dict, Any, Optional, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from ..core.agent_wrapper import get_agent
from ..database import get_database
from ..cache import get_cache
from .streaming_handler import get_streaming_handler
from ..utils.logger import get_logger
from ..utils.conversation_logger import get_conversation_logger


class WebSocketManager:
    """Manages WebSocket connections for voice communication."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.session_data: Dict[str, Dict[str, Any]] = {}  # session_id -> data
        self.streaming_handler = None
        self._initialized = False
        self.streaming_tasks: Dict[str, bool] = {}  # session_id -> should_stop_streaming

        # Error throttling (max 1 error per second per type)
        self.last_error_times: Dict[str, float] = {}
        self.error_throttle_seconds = 1.0

        # Logger
        self.logger = get_logger()

        # Conversation logger for comprehensive logging
        self.conversation_logger = get_conversation_logger()

        # Track TTS chunks per session
        self.tts_chunk_counts: Dict[str, int] = {}
    
    async def initialize(self):
        """Initialize the WebSocket manager."""
        if self._initialized:
            return

        self.db = await get_database()
        self.cache = await get_cache()
        self.agent = await get_agent()
        self.streaming_handler = get_streaming_handler()

        # Initialize SenseVoice model for ASR (only if USE_LOCAL_ASR=true)
        # On Render with USE_LOCAL_ASR=false, skip model loading entirely
        from ..config import get_settings
        settings = get_settings()

        if not settings.use_local_asr:
            self.logger.info("⚡ Local ASR disabled (USE_LOCAL_ASR=false), using HF Space only")
            self.conversation_logger.log_model_info(
                "sensevoice",
                loaded=False,
                error="Local ASR disabled, using HF Space API"
            )
        else:
            # Model will lazy-load on first use if available
            import os
            model_path = "models/iic/SenseVoiceSmall"

            # Check if model exists before trying to load
            if os.path.exists(model_path):
                self.logger.info(f"🔄 Loading SenseVoice model from {model_path}...")
                model_load_start = time.time()
                model_loaded = await self.streaming_handler.load_sensevoice_model(model_path)
                model_load_time = (time.time() - model_load_start) * 1000

                # Log model loading info
                if model_loaded:
                    self.logger.info("✅ SenseVoice model loaded successfully")
                    self.conversation_logger.log_model_info(
                        "sensevoice",
                        loaded=True,
                        model_path=model_path,
                        loading_time_ms=model_load_time
                    )
                else:
                    self.logger.warning(None, "⚠️ SenseVoice model failed to load - using fallback transcription")
                    self.conversation_logger.log_model_info(
                        "sensevoice",
                        loaded=False,
                        error="Model failed to load"
                    )
            else:
                self.logger.warning(None, f"⚠️ SenseVoice model not found at {model_path} - will use HF Space only")
                self.logger.warning(None, "   Run 'python scripts/download_sensevoice.py' to download the model for local use")
                self.conversation_logger.log_model_info(
                    "sensevoice",
                    loaded=False,
                    error=f"Model not found at {model_path}"
                )

        # Log agent info
        self.conversation_logger.log_model_info(
            "agent",
            loaded=True,
            model_path="NewsAgent"
        )

        self._initialized = True
        print("✅ WebSocketManager initialized successfully")
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID."""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def _should_log_error(self, error_key: str) -> bool:
        """Check if error should be logged (throttle to max 1 per second per type)."""
        current_time = time.time()
        last_time = self.last_error_times.get(error_key, 0)
        
        if current_time - last_time >= self.error_throttle_seconds:
            self.last_error_times[error_key] = current_time
            return True
        return False
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept WebSocket connection and create session."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # NOTE: WebSocket should already be accepted by the endpoint
            # Don't try to accept again here
            
            # Generate proper UUID for user_id if it's not already a UUID
            if user_id == "anonymous" or not self._is_valid_uuid(user_id):
                user_id = str(uuid.uuid4())
                self.logger.info(f"Generated UUID for anonymous user: {user_id[:8]}...")
            
            # Create new session
            session_id = str(uuid.uuid4())
            session_data = {
                "user_id": user_id,
                "websocket": websocket,
                "session_start": datetime.now(),
                "total_commands": 0,
                "total_interruptions": 0,
                "is_active": True
            }
            
            # Store connections
            self.active_connections[session_id] = websocket
            self.user_sessions[user_id] = session_id
            self.session_data[session_id] = session_data
            
            # Create session in database (non-fatal if it fails)
            try:
                await self.db.create_conversation_session(user_id)
            except Exception as db_err:
                # Log and continue – don't break the WebSocket connection
                self.logger.warning(session_id, f"Failed to create conversation session: {db_err}")
            
            self.logger.websocket_connect(session_id, user_id)

            # Start conversation logging session
            self.conversation_logger.start_session(session_id, user_id)

            # Small delay to ensure WebSocket is fully ready after accept
            await asyncio.sleep(0.01)
            
            # Send welcome message with retry
            connected_message = {
                "event": "connected",
                "data": {
                    "session_id": session_id,
                    "message": "Connected to Voice News Agent",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Try to send welcome message with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self.send_message(session_id, connected_message, raise_on_error=True)
                    self.logger.info(f"session={session_id[:8]}... | Successfully sent connected message (attempt {attempt + 1})")
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(session_id, f"Retry sending connected message (attempt {attempt + 1}): {e}")
                        await asyncio.sleep(0.05)  # Wait 50ms before retry
                    else:
                        self.logger.error(session_id, "send_connected_failed", f"All retries exhausted: {e}")
                        raise
            
            return session_id
            
        except Exception as e:
            print(f"❌ Error connecting WebSocket: {e}")
            raise
    
    async def disconnect(self, session_id: str):
        """Handle WebSocket disconnection."""
        try:
            if session_id in self.active_connections:
                # Update session end time
                if session_id in self.session_data:
                    self.session_data[session_id]["session_end"] = datetime.now()
                    self.session_data[session_id]["is_active"] = False
                
                # Remove from active connections
                websocket = self.active_connections.pop(session_id)
                
                # Remove user session mapping
                user_id = self.session_data.get(session_id, {}).get("user_id")
                if user_id and user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                
                # Clean up streaming buffers
                if self.streaming_handler:
                    self.streaming_handler.clear_session_buffer(session_id)
                
                # End conversation logging session
                self.conversation_logger.end_session(session_id)

                # Clean up session data
                if session_id in self.session_data:
                    del self.session_data[session_id]

                # Clean up TTS chunk count
                if session_id in self.tts_chunk_counts:
                    del self.tts_chunk_counts[session_id]

                print(f"✅ WebSocket disconnected: {session_id}")
                
        except Exception as e:
            print(f"❌ Error disconnecting WebSocket: {e}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any], raise_on_error: bool = False):
        """Send message to specific WebSocket connection.
        
        Args:
            session_id: Session ID
            message: Message dict to send
            raise_on_error: If True, raise exception on send failure (for retry logic)
        """
        try:
            if session_id not in self.active_connections:
                # Throttle this error (max 1 per second)
                if self._should_log_error(f"ws_not_found_{session_id}"):
                    self.logger.warning(session_id, "WebSocket not found, skipping message")
                if raise_on_error:
                    raise RuntimeError(f"WebSocket not found for session {session_id}")
                return
                
            websocket = self.active_connections[session_id]
            
            # Check if websocket is in correct state
            from starlette.websockets import WebSocketState
            if websocket.client_state != WebSocketState.CONNECTED:
                self.logger.warning(session_id, f"WebSocket not in CONNECTED state: {websocket.client_state.name}")
                if raise_on_error:
                    raise RuntimeError(f"WebSocket not in CONNECTED state: {websocket.client_state.name}")
                return
            
            # Log message being sent (DEBUG level)
            event = message.get("event", "unknown")
            self.logger.websocket_message_sent(session_id, event)
                
            await websocket.send_text(json.dumps(message))
                
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            if self._should_log_error(f"ws_send_error_{session_id}"):
                self.logger.error(session_id, "send_message_failed", error_msg)
            
            # If requested to raise, propagate the error for retry logic
            if raise_on_error:
                raise
            
            # Otherwise, only disconnect if WebSocket is actually closed
            if session_id in self.active_connections:
                websocket = self.active_connections[session_id]
                from starlette.websockets import WebSocketState
                if websocket.client_state == WebSocketState.DISCONNECTED:
                    self.logger.warning(session_id, "WebSocket disconnected, removing")
                    await self.disconnect(session_id)
    
    async def broadcast_message(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast message to all active connections."""
        exclude = exclude or set()
        
        for session_id in list(self.active_connections.keys()):
            if session_id not in exclude:
                await self.send_message(session_id, message)
    
    async def handle_voice_command(self, session_id: str, data: Dict[str, Any]):
        """Handle voice command from client."""
        try:
            if not self._initialized:
                await self.initialize()
            
            command = data.get("command", "")
            user_id = self.session_data.get(session_id, {}).get("user_id")
            
            if not user_id:
                await self.send_message(session_id, {
                    "event": "error",
                    "data": {
                        "error_type": "invalid_session",
                        "message": "Invalid session",
                        "session_id": session_id
                    }
                })
                return
            
            # Update session stats
            if session_id in self.session_data:
                self.session_data[session_id]["total_commands"] += 1
            
            # Send transcription confirmation
            await self.send_message(session_id, {
                "event": "transcription",
                "data": {
                    "text": command,
                    "confidence": data.get("confidence", 0.95),
                    "session_id": session_id,
                    "processing_time_ms": 150
                }
            })
            
            # Process command through agent
            start_time = datetime.now()
            result = await self.agent.process_voice_command(command, user_id, session_id)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Send text response first
            response_text = result["response_text"]
            await self.send_message(session_id, {
                "event": "voice_response",
                "data": {
                    "text": response_text,
                    "audio_url": result.get("audio_url"),
                    "response_type": result["response_type"],
                    "processing_time_ms": int(processing_time),
                    "session_id": session_id,
                    "news_items": result.get("news_items", []),
                    "stock_data": result.get("stock_data"),
                    "timestamp": datetime.now().isoformat(),
                    "streaming": True  # Indicate streaming TTS will follow
                }
            })
            
            # Stream TTS audio chunks
            await self.stream_tts_response(session_id, response_text)
            
        except Exception as e:
            print(f"❌ Error handling voice command: {e}")
            await self.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "command_processing_failed",
                    "message": str(e),
                    "session_id": session_id
                }
            })
    
    async def handle_voice_data(self, session_id: str, data: Dict[str, Any]):
        """Handle voice audio data from client (streaming mode)."""
        try:
            if not self._initialized:
                await self.initialize()
            
            audio_chunk_b64 = data.get("audio_chunk", "")
            is_final = data.get("is_final", False)
            user_id = self.session_data.get(session_id, {}).get("user_id")
            
            if not user_id:
                await self.send_message(session_id, {
                    "event": "error",
                    "data": {
                        "error_type": "invalid_session",
                        "message": "Invalid session",
                        "session_id": session_id
                    }
                })
                return
            
            # Decode audio chunk
            try:
                audio_chunk = base64.b64decode(audio_chunk_b64)
            except Exception as e:
                print(f"⚠️ Failed to decode audio chunk: {e}")
                audio_chunk = b""
            
            # Buffer and process audio
            full_buffer = await self.streaming_handler.buffer_audio_chunk(
                session_id, audio_chunk, is_final
            )
            
            if full_buffer:
                # Transcribe buffered audio
                transcribed_text = await self.streaming_handler.transcribe_chunk(
                    full_buffer,
                    format=data.get("format", "wav"),
                    sample_rate=data.get("format", 16000)
                )

                # Only send transcription if we got actual text (VAD passed)
                if transcribed_text:
                    # Send partial transcription
                    await self.send_message(session_id, {
                        "event": "partial_transcription",
                        "data": {
                            "text": transcribed_text,
                            "is_final": is_final,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                    })

                    # If final, process as command
                    if is_final:
                        await self.handle_voice_command(session_id, {
                            "command": transcribed_text,
                            "confidence": 0.90
                        })
                else:
                    # VAD rejected the audio (no speech detected)
                    print(f"🤫 Skipping empty transcription (VAD rejected audio)")
                    # Don't send error to frontend, just acknowledge
                    await self.send_message(session_id, {
                        "event": "audio_received",
                        "data": {
                            "session_id": session_id,
                            "vad_status": "no_speech",
                            "timestamp": datetime.now().isoformat()
                        }
                    })
            else:
                # Just acknowledge receipt for buffering
                await self.send_message(session_id, {
                    "event": "audio_received",
                    "data": {
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
            
        except Exception as e:
            print(f"❌ Error handling voice data: {e}")
            await self.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "audio_processing_failed",
                    "message": str(e),
                    "session_id": session_id
                }
            })
    
    async def handle_audio_chunk(self, session_id: str, data: Dict[str, Any]):
        """Handle audio chunk with complete ASR/LLM/TTS pipeline."""
        start_time = time.time()

        try:
            if not self._initialized:
                await self.initialize()

            user_id = self.session_data.get(session_id, {}).get("user_id")

            if not user_id:
                print(f"❌ No user_id found for session {session_id}")
                await self.send_message(session_id, {
                    "event": "error",
                    "data": {
                        "error_type": "invalid_session",
                        "message": "Invalid session",
                        "session_id": session_id
                    }
                })
                return

            # Decode audio chunk
            audio_chunk = base64.b64decode(data["audio_chunk"])
            audio_format = data.get("format", "webm")
            audio_size = len(audio_chunk)

            print(f"🎤 Processing audio chunk for session {session_id}: {audio_size} bytes ({audio_format})")

            # Process with streaming handler (ASR -> LLM -> TTS)
            result = await self.streaming_handler.process_voice_command(
                session_id, audio_chunk, audio_format
            )

            print(f"🎤 Processing result: {result}")

            if result["success"]:
                transcription = result["transcription"]
                agent_response = result["response"]

                # Send transcription
                await self.send_message(session_id, {
                    "event": "transcription",
                    "data": {
                        "text": transcription,
                        "confidence": 0.95,
                        "session_id": session_id,
                        "processing_time_ms": 200
                    }
                })

                # Send agent response
                await self.send_message(session_id, {
                    "event": "agent_response",
                    "data": {
                        "text": agent_response,
                        "session_id": session_id,
                        "processing_time_ms": 500,
                        "timestamp": result["timestamp"]
                    }
                })

                # Initialize TTS chunk count for this session
                self.tts_chunk_counts[session_id] = 0

                # Stream TTS response
                if agent_response:
                    print(f"🔊 Starting TTS streaming for: {agent_response[:50]}...")
                    await self.stream_tts_response(session_id, agent_response)

                # Calculate total processing time
                processing_time_ms = (time.time() - start_time) * 1000
                tts_chunks_sent = self.tts_chunk_counts.get(session_id, 0)

                # Log the complete conversation turn
                self.conversation_logger.log_conversation_turn(
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
                error_msg = result.get("error", "ASR processing failed")
                print(f"❌ Processing failed: {error_msg}")

                # Calculate processing time
                processing_time_ms = (time.time() - start_time) * 1000

                # Log failed turn
                self.conversation_logger.log_conversation_turn(
                    session_id=session_id,
                    user_id=user_id,
                    transcription="",
                    agent_response="",
                    processing_time_ms=processing_time_ms,
                    audio_format=audio_format,
                    audio_size_bytes=audio_size,
                    tts_chunks_sent=0,
                    error=error_msg
                )

                await self.send_message(session_id, {
                    "event": "error",
                    "data": {
                        "error_type": "asr_processing_failed",
                        "message": error_msg,
                        "session_id": session_id
                    }
                })

        except Exception as e:
            print(f"❌ Error handling audio chunk: {e}")

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Log error turn
            self.conversation_logger.log_conversation_turn(
                session_id=session_id,
                user_id=self.session_data.get(session_id, {}).get("user_id", "unknown"),
                transcription="",
                agent_response="",
                processing_time_ms=processing_time_ms,
                audio_format=data.get("format", "unknown"),
                audio_size_bytes=0,
                tts_chunks_sent=0,
                error=str(e)
            )

            await self.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "audio_processing_failed",
                    "message": str(e),
                    "session_id": session_id
                }
            })

    async def handle_audio_chunk_streaming(self, session_id: str, data: Dict[str, Any]):
        """
        Handle audio chunk with streaming LLM and concurrent TTS.
        This enables faster response by starting TTS as soon as LLM starts generating.
        """
        start_time = time.time()

        try:
            if not self._initialized:
                await self.initialize()

            user_id = self.session_data.get(session_id, {}).get("user_id")

            if not user_id:
                await self.send_message(session_id, {
                    "event": "error",
                    "data": {
                        "error_type": "invalid_session",
                        "message": "Invalid session",
                        "session_id": session_id
                    }
                })
                return

            # Decode audio chunk
            audio_chunk = base64.b64decode(data["audio_chunk"])
            audio_format = data.get("format", "webm")
            audio_size = len(audio_chunk)

            print(f"🎤 [STREAMING] Processing audio for session {session_id}: {audio_size} bytes ({audio_format})")

            # Reset interrupt flag for this session
            self.streaming_tasks[session_id] = False

            # Initialize counters
            chunk_index = 0
            transcription_text = ""
            full_response_text = ""

            # Process with streaming handler (ASR -> Streaming LLM -> Concurrent TTS)
            async for chunk in self.streaming_handler.process_voice_command_streaming(
                session_id, audio_chunk, audio_format
            ):
                # Check for interruption
                if self.streaming_tasks.get(session_id, False):
                    print(f"🛑 [STREAMING] Interrupted for session {session_id}")
                    break

                chunk_type = chunk.get("type")

                if chunk_type == "transcription":
                    transcription_text = chunk.get("text", "")
                    print(f"📝 [STREAMING] Transcription: {transcription_text}")

                    # Send transcription to client
                    await self.send_message(session_id, {
                        "event": "transcription",
                        "data": {
                            "text": transcription_text,
                            "confidence": 0.95,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                    })

                elif chunk_type == "text_chunk":
                    text_chunk = chunk.get("text", "")
                    full_response_text += text_chunk
                    print(f"💬 [STREAMING] Text chunk: {text_chunk[:50]}...")

                    # Send text chunk to client for display
                    await self.send_message(session_id, {
                        "event": "agent_response_chunk",
                        "data": {
                            "text": text_chunk,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                    })

                elif chunk_type == "audio_chunk":
                    audio_data = chunk.get("data")
                    print(f"🔊 [STREAMING] TTS chunk #{chunk_index}")

                    # Send audio chunk to client
                    await self.send_message(session_id, {
                        "event": "tts_chunk",
                        "data": {
                            "audio_chunk": base64.b64encode(audio_data).decode(),
                            "chunk_index": chunk_index,
                            "format": "mp3",
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                    chunk_index += 1

                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)

                elif chunk_type == "error":
                    error_msg = chunk.get("message", "Unknown error")
                    print(f"❌ [STREAMING] Error: {error_msg}")

                    await self.send_message(session_id, {
                        "event": "error",
                        "data": {
                            "error_type": "streaming_error",
                            "message": error_msg,
                            "session_id": session_id
                        }
                    })
                    return

                elif chunk_type == "complete":
                    print(f"✅ [STREAMING] Complete for session {session_id}")

                    # Send completion message
                    await self.send_message(session_id, {
                        "event": "tts_complete",
                        "data": {
                            "session_id": session_id,
                            "total_chunks": chunk_index,
                            "timestamp": datetime.now().isoformat()
                        }
                    })

            # Calculate total processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Log the conversation turn
            self.conversation_logger.log_conversation_turn(
                session_id=session_id,
                user_id=user_id,
                transcription=transcription_text,
                agent_response=full_response_text,
                processing_time_ms=processing_time_ms,
                audio_format=audio_format,
                audio_size_bytes=audio_size,
                tts_chunks_sent=chunk_index,
                metadata={
                    "streaming": True,
                    "interrupted": self.streaming_tasks.get(session_id, False)
                }
            )

            print(f"📊 [STREAMING] Completed in {processing_time_ms:.0f}ms, {chunk_index} TTS chunks")

        except Exception as e:
            print(f"❌ [STREAMING] Error handling audio chunk: {e}")
            import traceback
            traceback.print_exc()

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Log error turn
            self.conversation_logger.log_conversation_turn(
                session_id=session_id,
                user_id=self.session_data.get(session_id, {}).get("user_id", "unknown"),
                transcription="",
                agent_response="",
                processing_time_ms=processing_time_ms,
                audio_format=data.get("format", "unknown"),
                audio_size_bytes=0,
                tts_chunks_sent=0,
                error=str(e)
            )

            await self.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "streaming_processing_failed",
                    "message": str(e),
                    "session_id": session_id
                }
            })

    async def handle_interrupt(self, session_id: str, data: Dict[str, Any]):
        """Handle voice interruption."""
        try:
            if session_id in self.session_data:
                self.session_data[session_id]["total_interruptions"] += 1

            # Log interruption
            self.conversation_logger.log_interruption(session_id)

            # Signal to stop any ongoing TTS streaming
            self.streaming_tasks[session_id] = True
            print(f"⚠️ Interrupt signal sent for session {session_id}")
            
            # Send interruption confirmation
            await self.send_message(session_id, {
                "event": "voice_interrupted",
                "data": {
                    "session_id": session_id,
                    "reason": data.get("reason", "user_interruption"),
                    "interruption_time_ms": 85,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ Error handling interrupt: {e}")
    
    async def handle_start_listening(self, session_id: str, data: Dict[str, Any]):
        """Handle start listening command."""
        try:
            await self.send_message(session_id, {
                "event": "listening_started",
                "data": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ Error handling start listening: {e}")
    
    async def handle_stop_listening(self, session_id: str, data: Dict[str, Any]):
        """Handle stop listening command."""
        try:
            await self.send_message(session_id, {
                "event": "listening_stopped",
                "data": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"❌ Error handling stop listening: {e}")
    
    async def process_message(self, websocket: WebSocket, message: str):
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            event = data.get("event")
            session_id = data.get("data", {}).get("session_id")
            
            if not session_id:
                self.logger.warning(None, "No session_id in message")
                return
            
            # Check if session is still active
            if session_id not in self.active_connections:
                self.logger.warning(session_id, "Session no longer active, ignoring message")
                return
            
            # Log message received
            self.logger.websocket_message_received(session_id, event)
            
            # Route message to appropriate handler
            if event == "voice_command":
                await self.handle_voice_command(session_id, data.get("data", {}))
            elif event == "voice_data":
                await self.handle_voice_data(session_id, data.get("data", {}))
            elif event == "audio_chunk":
                await self.handle_audio_chunk(session_id, data.get("data", {}))
            elif event == "audio_chunk_streaming":
                await self.handle_audio_chunk_streaming(session_id, data.get("data", {}))
            elif event == "interrupt":
                await self.handle_interrupt(session_id, data.get("data", {}))
            elif event == "start_listening":
                await self.handle_start_listening(session_id, data.get("data", {}))
            elif event == "stop_listening":
                await self.handle_stop_listening(session_id, data.get("data", {}))
            else:
                print(f"⚠️ Unknown event: {event}")
                
        except json.JSONDecodeError:
            print("❌ Invalid JSON in WebSocket message")
        except Exception as e:
            print(f"❌ Error processing WebSocket message: {e}")
    
    def get_active_connections_count(self) -> int:
        """Get count of active connections."""
        return len(self.active_connections)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return self.session_data.get(session_id)
    
    def get_user_session(self, user_id: str) -> Optional[str]:
        """Get session ID for user."""
        return self.user_sessions.get(user_id)
    
    async def stream_tts_response(self, session_id: str, text: str):
        """Stream TTS audio back to client in chunks.
        
        Supports real-time interruption: when user starts speaking while agent
        is talking, the interrupt handler sets streaming_tasks[session_id] = True,
        which causes this loop to break immediately and stop sending TTS chunks.
        """
        try:
            if not self.streaming_handler:
                print("⚠️ Streaming handler not initialized")
                return
            
            # Reset interrupt flag before starting new response
            # This ensures each new response starts fresh and can be interrupted
            self.streaming_tasks[session_id] = False

            chunk_index = 0
            total_chunks_sent = 0
            interrupted = False

            async for audio_chunk in self.streaming_handler.stream_tts_audio(text):
                # Check for interrupt signal on each chunk
                # This allows near-instant interruption when user speaks
                if self.streaming_tasks.get(session_id, False):
                    print(f"🛑 TTS streaming interrupted for {session_id}")
                    interrupted = True
                    break

                # Send audio chunk
                await self.send_message(session_id, {
                    "event": "tts_chunk",
                    "data": {
                        "audio_chunk": base64.b64encode(audio_chunk).decode(),
                        "chunk_index": chunk_index,
                        "format": "mp3",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                chunk_index += 1
                total_chunks_sent += 1

                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)

            # Update TTS chunk count for this session
            self.tts_chunk_counts[session_id] = total_chunks_sent
            
            # Send streaming complete or interrupted event
            if interrupted:
                await self.send_message(session_id, {
                    "event": "streaming_interrupted",
                    "data": {
                        "total_chunks_sent": total_chunks_sent,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                print(f"⚠️ Streaming interrupted after {total_chunks_sent} chunks for {session_id}")
            else:
                await self.send_message(session_id, {
                    "event": "streaming_complete",
                    "data": {
                        "total_chunks_sent": total_chunks_sent,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                print(f"✅ Streamed {total_chunks_sent} TTS chunks to {session_id}")
            
        except Exception as e:
            print(f"❌ Error streaming TTS: {e}")
            await self.send_message(session_id, {
                "event": "error",
                "data": {
                    "error_type": "tts_streaming_failed",
                    "message": str(e),
                    "session_id": session_id
                }
            })


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance."""
    if not websocket_manager._initialized:
        await websocket_manager.initialize()
    return websocket_manager
