"""Streaming voice handler for real-time audio processing."""
import asyncio
import base64
import hashlib
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from funasr import AutoModel
except ImportError:
    AutoModel = None

try:
    from .hf_space_asr import get_hf_space_asr
    HF_SPACE_AVAILABLE = True
except ImportError:
    HF_SPACE_AVAILABLE = False

try:
    from .audio_validator import get_audio_validator
    AUDIO_VALIDATOR_AVAILABLE = True
except ImportError:
    AUDIO_VALIDATOR_AVAILABLE = False


class StreamingVoiceHandler:
    """Handle streaming voice input/output."""

    def __init__(self):
        self.audio_buffers = {}  # session_id -> buffer
        self.transcription_cache = {}  # session_id -> partial text
        self.sensevoice_model = None
        self._model_loaded = False
        self.hf_space_asr = None
        self._hf_space_enabled = True  # Prefer HF Space by default
        self.audio_validator = None

        # Get configuration
        from ..config import get_settings
        self.settings = get_settings()
        self._use_local_asr = self.settings.use_local_asr

        # Initialize audio validator
        if AUDIO_VALIDATOR_AVAILABLE:
            self.audio_validator = get_audio_validator(
                energy_threshold=500.0,
                vad_mode=3,
                enable_webrtc_vad=True
            )
    
    async def load_sensevoice_model(self, model_path: str = "models/SenseVoiceSmall"):
        """Load SenseVoice model for ASR (same as src implementation)."""
        if AutoModel is None:
            print("⚠️ FunASR not available, using fallback ASR")
            return False
            
        try:
            print(f"🔄 Loading SenseVoice model: {model_path}")
            self.sensevoice_model = AutoModel(
                model=model_path,
                trust_remote_code=True
            )
            self._model_loaded = True
            print("✅ SenseVoice model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load SenseVoice model: {e}")
            return False
    
    async def stream_tts_audio(
        self, 
        text: str, 
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
        chunk_size: int = 4096
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS audio in chunks using Edge-TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use
            rate: Speech rate adjustment
            chunk_size: Size of each chunk in bytes
            
        Yields:
            Audio chunks as bytes
        """
        if edge_tts is None:
            # Fallback: return empty chunks if edge-tts not available
            print("⚠️ edge-tts not available, skipping TTS streaming")
            return
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            
            buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.extend(chunk["data"])
                    
                    # Yield chunks of specified size
                    while len(buffer) >= chunk_size:
                        yield bytes(buffer[:chunk_size])
                        buffer = buffer[chunk_size:]
            
            # Yield remaining data
            if buffer:
                yield bytes(buffer)
                
        except Exception as e:
            print(f"❌ Error streaming TTS: {e}")
            raise
    
    async def buffer_audio_chunk(
        self, 
        session_id: str, 
        audio_chunk: bytes,
        is_final: bool = False
    ) -> Optional[bytes]:
        """
        Buffer incoming audio chunks and return full buffer when ready.
        
        Args:
            session_id: Session identifier
            audio_chunk: Audio data chunk
            is_final: Whether this is the final chunk
            
        Returns:
            Full audio buffer if ready for processing, None otherwise
        """
        if session_id not in self.audio_buffers:
            self.audio_buffers[session_id] = bytearray()
        
        self.audio_buffers[session_id].extend(audio_chunk)
        
        # Process if buffer is large enough (1 second at 16kHz, 16-bit)
        # or if final chunk
        buffer_size_threshold = 32000  # ~1 second of audio
        
        if len(self.audio_buffers[session_id]) >= buffer_size_threshold or is_final:
            full_buffer = bytes(self.audio_buffers[session_id])
            self.audio_buffers[session_id].clear()
            return full_buffer
        
        return None
    
    async def transcribe_chunk(
        self,
        audio_data: bytes,
        format: str = "wav",
        sample_rate: int = 16000,
        validate_audio: bool = True
    ) -> str:
        """
        Transcribe audio chunk with support for compressed formats.

        Uses HuggingFace Space as primary ASR, falls back to local model.

        Args:
            audio_data: Raw audio bytes (may be compressed)
            format: Audio format (wav, opus, webm, mp3, etc.)
            sample_rate: Sample rate in Hz
            validate_audio: Enable audio validation (energy + WebRTC VAD)

        Returns:
            Transcribed text
        """
        # Validate audio quality before processing
        if validate_audio and self.audio_validator and format in ["wav", "pcm"]:
            is_valid, validation_info = self.audio_validator.validate_audio(
                audio_data,
                sample_rate=sample_rate,
                format=format
            )

            if not is_valid:
                reason = validation_info.get("reason", "unknown")
                energy = validation_info.get("energy", 0)
                print(f"⚠️ Audio validation failed: {reason} (energy={energy:.1f})")
                raise RuntimeError(f"Audio validation failed: {reason}")


        # Try HuggingFace Space first (preferred for production)
        if self._hf_space_enabled and HF_SPACE_AVAILABLE:
            try:
                if self.hf_space_asr is None:
                    self.hf_space_asr = get_hf_space_asr()

                # Convert to WAV if needed
                wav_data = await self._convert_to_wav(audio_data, format, sample_rate)

                print(f"🌐 Using HF Space ASR: {len(audio_data)} bytes ({format})")

                # Transcribe using HF Space
                transcription = await self.hf_space_asr.transcribe_audio_bytes(
                    wav_data,
                    sample_rate=sample_rate,
                    format="wav"
                )

                print(f"✓ HF Space transcribed: '{transcription}'")
                return transcription

            except Exception as e:
                print(f"⚠️ HF Space ASR failed: {e}")

                # Only fallback if local ASR is enabled
                if not self._use_local_asr:
                    print(f"❌ Local ASR disabled (USE_LOCAL_ASR=false), no fallback available")
                    raise RuntimeError("HF Space ASR failed and local ASR is disabled")

                print(f"   Falling back to local model...")

        # Fallback to local model (only if enabled)
        if not self._use_local_asr:
            print(f"❌ Local ASR disabled (USE_LOCAL_ASR=false)")
            raise RuntimeError("Speech recognition unavailable. HF Space failed and local ASR is disabled.")

        if not self._model_loaded or self.sensevoice_model is None:
            print(f"❌ No ASR available (HF Space failed, local model not loaded)")
            raise RuntimeError("Speech recognition unavailable. Please check configuration.")

        try:
            # Convert compressed audio to WAV if needed
            wav_data = await self._convert_to_wav(audio_data, format, sample_rate)

            # Save audio to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                tmpfile.write(wav_data)
                audio_file = tmpfile.name

            print(f"🎤 Using local model: {len(audio_data)} bytes ({format}) -> {len(wav_data)} bytes (wav)")

            # Transcribe with local SenseVoice
            result = self.sensevoice_model.generate(
                input=audio_file,
                cache={},
                language="auto",
                use_itn=False,
            )

            # Clean up temp file
            import os
            os.unlink(audio_file)

            if result and len(result) > 0 and 'text' in result[0]:
                # Extract text (remove language tags)
                text = result[0]['text'].split(">")[-1].strip()
                print(f"✓ Local model transcribed: '{text}'")
                return text
            else:
                raise RuntimeError("Transcription model returned empty result")

        except Exception as e:
            print(f"❌ Transcription error: {e}")
            raise
    
    async def _convert_to_wav(self, audio_data: bytes, format: str, sample_rate: int = 16000) -> bytes:
        """
        Convert compressed audio to WAV format using FFmpeg.
        
        Args:
            audio_data: Raw audio bytes
            format: Source format (opus, webm, mp3, etc.)
            sample_rate: Target sample rate
            
        Returns:
            WAV audio bytes
        """
        import tempfile
        import subprocess
        import os
        
        # If already WAV, return as-is
        if format.lower() == "wav":
            return audio_data
        
        input_path = None
        output_path = None

        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as input_file:
                input_file.write(audio_data)
                input_path = input_file.name

            print(f"📁 Created temp input file: {input_path} ({len(audio_data)} bytes)")

            # DEBUG: Save a copy for inspection
            debug_path = f"/tmp/debug_audio_{os.path.basename(input_path)}"
            import shutil
            shutil.copy(input_path, debug_path)
            print(f"🐛 DEBUG: Saved copy to {debug_path}")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as output_file:
                output_path = output_file.name

            print(f"📁 Created temp output file: {output_path}")

            # FFmpeg command to convert to WAV with better error handling
            ffmpeg_cmd = [
                'ffmpeg',
                '-v', 'error',  # Only show errors
                '-i', input_path,
                '-ar', str(sample_rate),
                '-ac', '1',  # Mono
                '-f', 'wav',
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-y',  # Overwrite output
                output_path
            ]

            print(f"🔧 Running FFmpeg: {' '.join(ffmpeg_cmd)}")

            # Run FFmpeg conversion
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
            
            # Read converted WAV data
            with open(output_path, 'rb') as f:
                wav_data = f.read()
            
            # Clean up temp files
            os.unlink(input_path)
            os.unlink(output_path)
            
            print(f"✅ Converted {format} to WAV: {len(audio_data)} -> {len(wav_data)} bytes")
            return wav_data
            
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg conversion failed: {e.stderr}")
            print(f"   Input file: {input_path} exists={os.path.exists(input_path) if input_path else 'N/A'}")
            print(f"   Output file: {output_path} exists={os.path.exists(output_path) if output_path else 'N/A'}")
            # Re-raise error instead of returning bad data
            raise RuntimeError(f"FFmpeg conversion failed: {e.stderr}")
        except Exception as e:
            print(f"❌ Audio conversion error: {e}")
            raise RuntimeError(f"Audio conversion error: {e}")
        finally:
            # Ensure temp files are cleaned up
            try:
                if input_path and os.path.exists(input_path):
                    os.unlink(input_path)
                if output_path and os.path.exists(output_path):
                    os.unlink(output_path)
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup temp files: {cleanup_error}")
    
    async def process_voice_command(
        self, 
        session_id: str, 
        audio_chunk: bytes, 
        format: str = "webm"
    ) -> Dict[str, Any]:
        """
        Process incoming audio chunk through ASR, LLM, and TTS.
        This method orchestrates the full voice pipeline.
        """
        from ..core.agent_wrapper import get_agent # Lazy import to avoid circular dependency
        agent = await get_agent()
        
        try:
            # 1. ASR: Transcribe audio chunk
            transcription = await self.transcribe_chunk(audio_chunk, format)
            
            if not transcription:
                return {"success": False, "error": "No transcription"}
            
            # 2. LLM: Get agent response
            user_id = "anonymous" # TODO: Get actual user_id from session
            response_result = await agent.process_voice_command(transcription, user_id, session_id)
            response_text = response_result.get("response_text", "I'm sorry, I couldn't process that.")
            
            return {
                "success": True,
                "transcription": transcription,
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error in full voice pipeline: {e}")
            return {"success": False, "error": str(e)}
    
    def clear_session_buffer(self, session_id: str):
        """Clear audio buffer for a session."""
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
        if session_id in self.transcription_cache:
            del self.transcription_cache[session_id]
    
    async def process_partial_transcription(
        self,
        session_id: str,
        partial_text: str,
        is_final: bool = False
    ) -> str:
        """
        Process partial transcription results.
        
        Args:
            session_id: Session identifier
            partial_text: Partial transcription
            is_final: Whether this is final
            
        Returns:
            Accumulated transcription text
        """
        if session_id not in self.transcription_cache:
            self.transcription_cache[session_id] = ""
        
        if is_final:
            # Return final text and clear cache
            final_text = self.transcription_cache[session_id] + " " + partial_text
            del self.transcription_cache[session_id]
            return final_text.strip()
        else:
            # Accumulate partial results
            self.transcription_cache[session_id] += " " + partial_text
            return self.transcription_cache[session_id].strip()
    
    def get_stream_stats(self) -> dict:
        """Get statistics about active streams."""
        return {
            "active_buffers": len(self.audio_buffers),
            "total_buffer_size": sum(len(buf) for buf in self.audio_buffers.values()),
            "active_transcriptions": len(self.transcription_cache)
        }


# Global streaming handler instance
streaming_handler = StreamingVoiceHandler()


def get_streaming_handler() -> StreamingVoiceHandler:
    """Get streaming handler instance."""
    return streaming_handler

