"""Voice-related Pydantic models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class VoiceCommand(BaseModel):
    """Voice command model."""
    command: str = Field(..., description="Voice command text")
    confidence: Optional[float] = Field(None, description="Recognition confidence")
    language: Optional[str] = Field(default="en-US", description="Language code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Command timestamp")


class VoiceTranscription(BaseModel):
    """Voice transcription model."""
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Transcription confidence")
    language: str = Field(default="en-US", description="Detected language")
    processing_time_ms: int = Field(..., description="Processing time")
    audio_duration_ms: Optional[int] = Field(None, description="Audio duration")
    timestamp: datetime = Field(default_factory=datetime.now, description="Transcription timestamp")


class VoiceSynthesis(BaseModel):
    """Voice synthesis model."""
    text: str = Field(..., description="Text to synthesize")
    voice: str = Field(default="en-US-AriaNeural", description="Voice type")
    rate: float = Field(default=1.0, description="Speech rate")
    pitch: float = Field(default=1.0, description="Speech pitch")
    volume: float = Field(default=1.0, description="Speech volume")
    format: str = Field(default="mp3", description="Audio format")


class VoiceSynthesisResponse(BaseModel):
    """Voice synthesis response model."""
    audio_url: str = Field(..., description="Generated audio URL")
    audio_duration_ms: int = Field(..., description="Audio duration")
    processing_time_ms: int = Field(..., description="Processing time")
    text_length: int = Field(..., description="Input text length")
    voice: str = Field(..., description="Used voice")
    timestamp: datetime = Field(default_factory=datetime.now, description="Synthesis timestamp")


class VoiceInterruption(BaseModel):
    """Voice interruption model."""
    session_id: str = Field(..., description="Session ID")
    reason: str = Field(..., description="Interruption reason")
    interruption_time_ms: int = Field(..., description="Interruption response time")
    timestamp: datetime = Field(default_factory=datetime.now, description="Interruption timestamp")


class VoiceSession(BaseModel):
    """Voice session model."""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    session_start: datetime = Field(..., description="Session start time")
    session_end: Optional[datetime] = Field(None, description="Session end time")
    total_commands: int = Field(default=0, description="Total voice commands")
    total_interruptions: int = Field(default=0, description="Total interruptions")
    average_response_time_ms: float = Field(default=0.0, description="Average response time")
    is_active: bool = Field(default=True, description="Session active status")


class VoiceAudioData(BaseModel):
    """Voice audio data model."""
    audio_chunk: str = Field(..., description="Base64 encoded audio chunk")
    format: str = Field(default="wav", description="Audio format")
    sample_rate: int = Field(default=16000, description="Sample rate")
    channels: int = Field(default=1, description="Audio channels")
    duration_ms: Optional[int] = Field(None, description="Audio duration")
    timestamp: datetime = Field(default_factory=datetime.now, description="Audio timestamp")


class VoiceSettings(BaseModel):
    """Voice settings model."""
    speech_rate: float = Field(default=1.0, description="Speech rate multiplier")
    voice_type: str = Field(default="en-US-AriaNeural", description="Voice type")
    interruption_sensitivity: float = Field(default=0.5, description="Interruption sensitivity")
    auto_play: bool = Field(default=True, description="Auto-play responses")
    noise_reduction: bool = Field(default=True, description="Noise reduction")
    echo_cancellation: bool = Field(default=True, description="Echo cancellation")

    # VAD Configuration
    voice_activity_detection: bool = Field(default=True, description="Voice activity detection")
    vad_threshold: float = Field(default=0.02, ge=0.01, le=0.1, description="VAD speech threshold (0.01-0.1)")
    silence_timeout_ms: int = Field(default=700, ge=300, le=2000, description="Silence timeout (300-2000ms)")
    min_recording_duration_ms: int = Field(default=500, ge=300, le=2000, description="Minimum recording duration (300-2000ms)")
    vad_check_interval_ms: int = Field(default=250, ge=100, le=500, description="VAD check interval (100-500ms)")

    # Backend VAD Validation
    backend_vad_enabled: bool = Field(default=True, description="Enable backend WebRTC VAD validation")
    backend_vad_mode: int = Field(default=3, ge=0, le=3, description="WebRTC VAD aggressiveness (0-3)")
    backend_energy_threshold: float = Field(default=500.0, description="Backend energy threshold for pre-filtering")

    # Audio Compression
    use_compression: bool = Field(default=False, description="Enable Opus compression")
    compression_codec: str = Field(default="opus", description="Compression codec (opus, webm)")
    compression_bitrate: int = Field(default=64000, description="Compression bitrate in bps")


class VoiceCommandRequest(BaseModel):
    """Voice command request model."""
    command: str = Field(..., description="Voice command")
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    confidence: Optional[float] = Field(None, description="Command confidence")
    language: Optional[str] = Field(default="en-US", description="Language code")
    context: Optional[Dict[str, Any]] = Field(None, description="Command context")


class VoiceCommandResponse(BaseModel):
    """Voice command response model."""
    response_text: str = Field(..., description="Response text")
    audio_url: Optional[str] = Field(None, description="Response audio URL")
    response_type: str = Field(..., description="Response type")
    processing_time_ms: int = Field(..., description="Processing time")
    session_id: str = Field(..., description="Session ID")
    news_items: Optional[List[Dict[str, Any]]] = Field(None, description="Related news items")
    stock_data: Optional[Dict[str, Any]] = Field(None, description="Related stock data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class VoiceError(BaseModel):
    """Voice error model."""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")


class VoiceAnalytics(BaseModel):
    """Voice analytics model."""
    user_id: str = Field(..., description="User ID")
    total_sessions: int = Field(default=0, description="Total voice sessions")
    total_commands: int = Field(default=0, description="Total voice commands")
    total_interruptions: int = Field(default=0, description="Total interruptions")
    average_session_duration_minutes: float = Field(default=0.0, description="Average session duration")
    average_response_time_ms: float = Field(default=0.0, description="Average response time")
    most_used_commands: List[str] = Field(default=[], description="Most used commands")
    recognition_accuracy: float = Field(default=0.0, description="Recognition accuracy")
    interruption_rate: float = Field(default=0.0, description="Interruption rate")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")
