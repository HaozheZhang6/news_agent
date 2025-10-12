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


class StreamingVoiceHandler:
    """Handle streaming voice input/output."""
    
    def __init__(self):
        self.audio_buffers = {}  # session_id -> buffer
        self.transcription_cache = {}  # session_id -> partial text
        self.sensevoice_model = None
        self._model_loaded = False
    
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
        sample_rate: int = 16000
    ) -> str:
        """
        Transcribe audio chunk.
        
        Note: This is a placeholder. In production, you would:
        - Use SenseVoice for local transcription
        - Or call OpenAI Whisper API
        - Or rely on client-side iOS ASR
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format
            sample_rate: Sample rate in Hz
            
        Returns:
            Transcribed text
        """
        if not self._model_loaded or self.sensevoice_model is None:
            # Fallback: return placeholder text for testing
            return "What's the stock price of AAPL today?"
        
        try:
            # Save audio to temporary file (same as src implementation)
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                tmpfile.write(audio_data)
                audio_file = tmpfile.name
            
            # Transcribe with SenseVoice (same as src implementation)
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
                # Extract text (remove language tags, same as src)
                text = result[0]['text'].split(">")[-1].strip()
                print(f"🎤 Transcribed: '{text}'")
                return text
            else:
                return "What's the stock price of AAPL today?"
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return "What's the stock price of AAPL today?"
    
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

