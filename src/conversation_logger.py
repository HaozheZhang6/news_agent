"""Conversation logging utilities for user-agent dialogue history."""
import logging
from datetime import datetime
from pathlib import Path
from .config import CONVERSATIONS_DIR, LOGS_DIR


class ConversationLogger:
    def __init__(self):
        self.setup_loggers()
        
    def setup_loggers(self):
        """Setup both conversation and application loggers."""
        # Application logger for technical events
        self.app_logger = logging.getLogger('news_agent')
        self.app_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.app_logger.handlers.clear()
        
        # File handler for application logs
        app_handler = logging.FileHandler(LOGS_DIR / 'app.log')
        app_handler.setLevel(logging.INFO)
        app_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        app_handler.setFormatter(app_formatter)
        self.app_logger.addHandler(app_handler)
        
        # Console handler for application logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(app_formatter)
        self.app_logger.addHandler(console_handler)
        
        # Conversation logger - separate file per day
        self.conversation_file = None
        self.current_date = None
        
    def get_conversation_file(self):
        """Get current conversation file, create new one if date changed."""
        today = datetime.now().strftime("%Y%m%d")
        
        if self.current_date != today or self.conversation_file is None:
            self.current_date = today
            self.conversation_file = CONVERSATIONS_DIR / f"conversation_{today}.txt"
            
            # Create file if it doesn't exist
            if not self.conversation_file.exists():
                with open(self.conversation_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Conversation Log - {today}\n\n")
                    
        return self.conversation_file
    
    def _log_conversation(self, speaker: str, text: str, audio_file: str = None):
        """Internal method to log conversation entries."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conv_file = self.get_conversation_file()
        
        with open(conv_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {speaker}: \"{text}\"\n")
            if audio_file:
                f.write(f"    Audio: {audio_file}\n")
    
    def log_user_input(self, text: str, audio_file: str = None):
        """Log user input to conversation file."""
        self._log_conversation("USER", text, audio_file)
        self.app_logger.info(f"User input: {text}")
        if audio_file:
            self.app_logger.info(f"Audio saved: {audio_file}")
    
    def log_agent_response(self, text: str, audio_file: str = None):
        """Log agent response to conversation file."""
        self._log_conversation("AGENT", text, audio_file)
        self.app_logger.info(f"Agent response: {text}")
        if audio_file:
            self.app_logger.info(f"Response audio: {audio_file}")
    
    def log_system_event(self, event: str):
        """Log system events like interruptions."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conv_file = self.get_conversation_file()
        
        with open(conv_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] SYSTEM: {event}\n")
            
        # Also log to application logger
        self.app_logger.info(f"System event: {event}")
    
    def log_vad_activity(self, active: bool, timestamp: float = None):
        """Log Voice Activity Detection results."""
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        status = "active" if active else "inactive"
        self.app_logger.debug(f"VAD: {status} at {timestamp}")
    
    def log_error(self, error: str, exception: Exception = None):
        """Log errors."""
        self.app_logger.error(f"Error: {error}")
        if exception:
            self.app_logger.exception(exception)
    
    def log_interruption(self, reason: str):
        """Log interruption events."""
        self.log_system_event(f"Audio playback interrupted: {reason}")


# Global conversation logger instance
conversation_logger = ConversationLogger()