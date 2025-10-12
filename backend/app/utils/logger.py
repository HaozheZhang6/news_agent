"""Logging utility for Voice News Agent Backend."""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

class VoiceAgentLogger:
    """Custom logger for voice agent with detailed flow tracking."""
    
    def __init__(self, name: str = "voice_agent"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs/detailed")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler for detailed logs with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"backend_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def websocket_connect(self, session_id: str, user_id: str):
        """Log WebSocket connection."""
        self.logger.info(f"🔌 WS_CONNECT | session={session_id[:8]}... | user={user_id[:8]}...")
    
    def websocket_disconnect(self, session_id: str):
        """Log WebSocket disconnection."""
        self.logger.info(f"🔌 WS_DISCONNECT | session={session_id[:8]}...")
    
    def websocket_message_received(self, session_id: str, event: str):
        """Log WebSocket message received."""
        self.logger.debug(f"📥 WS_RECV | session={session_id[:8]}... | event={event}")
    
    def websocket_message_sent(self, session_id: str, event: str):
        """Log WebSocket message sent."""
        self.logger.debug(f"📤 WS_SEND | session={session_id[:8]}... | event={event}")
    
    def audio_received(self, session_id: str, size_bytes: int):
        """Log audio chunk received."""
        self.logger.debug(f"🎤 AUDIO_RECV | session={session_id[:8]}... | size={size_bytes} bytes")
    
    def audio_sent(self, session_id: str, chunk_index: int):
        """Log audio chunk sent."""
        self.logger.debug(f"🔊 AUDIO_SEND | session={session_id[:8]}... | chunk={chunk_index}")
    
    def transcription(self, session_id: str, text: str):
        """Log transcription."""
        self.logger.info(f"📝 TRANSCRIPTION | session={session_id[:8]}... | text='{text[:50]}...'")
    
    def llm_response(self, session_id: str, text: str):
        """Log LLM response."""
        self.logger.info(f"🤖 LLM_RESPONSE | session={session_id[:8]}... | text='{text[:50]}...'")
    
    def interruption(self, session_id: str, reason: str):
        """Log interruption."""
        self.logger.info(f"🛑 INTERRUPT | session={session_id[:8]}... | reason={reason}")
    
    def error(self, session_id: Optional[str], error_type: str, message: str):
        """Log error."""
        session = session_id[:8] + "..." if session_id else "unknown"
        self.logger.error(f"❌ ERROR | session={session} | type={error_type} | msg={message}")
    
    def warning(self, session_id: Optional[str], message: str):
        """Log warning."""
        session = session_id[:8] + "..." if session_id else "unknown"
        self.logger.warning(f"⚠️ WARNING | session={session} | msg={message}")
    
    def info(self, message: str):
        """Log general info."""
        self.logger.info(f"ℹ️ INFO | {message}")
    
    def debug(self, message: str):
        """Log debug info."""
        self.logger.debug(f"🔍 DEBUG | {message}")


# Global logger instance
voice_logger = VoiceAgentLogger()


def get_logger() -> VoiceAgentLogger:
    """Get the voice agent logger."""
    return voice_logger

