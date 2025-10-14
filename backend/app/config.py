"""Configuration management for Voice News Agent Backend."""
import os
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


def get_sensevoice_model_path() -> str:
    """Get the SenseVoice model path, auto-detecting if not set."""
    # Check if explicitly set via environment variable
    if os.getenv("SENSEVOICE_MODEL_PATH"):
        return os.getenv("SENSEVOICE_MODEL_PATH")
    
    # Try to find the model in ModelScope cache
    try:
        from modelscope.hub.snapshot_download import snapshot_download
        cache_dir = Path.home() / ".cache" / "modelscope" / "hub"
        model_path = snapshot_download(
            model_id="iic/SenseVoiceSmall",
            cache_dir=str(cache_dir),
            revision="master"
        )
        return str(model_path)
    except Exception:
        # Fallback to default path
        return "/app/models/SenseVoiceSmall"


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Database Configuration (Supabase)
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_key: str = Field(default="", env="SUPABASE_KEY")  # Now set to service key in env files
    supabase_service_key: str = Field(default="", env="SUPABASE_SERVICE_KEY")
    supabase_db_password: Optional[str] = Field(default=None, env="SUPABASE_DB_PASSWORD")
    
    # Cache Configuration (Upstash Redis)
    upstash_redis_rest_url: str = Field(default="", env="UPSTASH_REDIS_REST_URL")
    upstash_redis_rest_token: str = Field(default="", env="UPSTASH_REDIS_REST_TOKEN")
    upstash_redis_rest_read_only_url: Optional[str] = Field(default=None, env="UPSTASH_REDIS_REST_READ_ONLY_URL")
    upstash_redis_rest_read_only_token: Optional[str] = Field(default=None, env="UPSTASH_REDIS_REST_READ_ONLY_TOKEN")
    
    # AI Services
    zhipuai_api_key: str = Field(default="placeholder", env="ZHIPUAI_API_KEY")
    alphavantage_api_key: str = Field(default="placeholder", env="ALPHAVANTAGE_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Voice Services
    sensevoice_model_path: str = Field(default_factory=get_sensevoice_model_path, env="SENSEVOICE_MODEL_PATH")
    use_local_asr: bool = Field(default=True, env="USE_LOCAL_ASR")  # False on Render (use HF Space only)
    hf_token: Optional[str] = Field(default=None, env="HF_TOKEN")  # HuggingFace token for Space API
    hf_space_name: str = Field(default="hz6666/SenseVoiceSmall", env="HF_SPACE_NAME")
    edge_tts_voice: str = Field(default="en-US-AriaNeural", env="EDGE_TTS_VOICE")
    edge_tts_rate: float = Field(default=1.0, env="EDGE_TTS_RATE")
    edge_tts_pitch: float = Field(default=1.0, env="EDGE_TTS_PITCH")
    
    # Audio Configuration
    audio_rate: int = Field(default=16000, env="AUDIO_RATE")
    audio_channels: int = Field(default=1, env="AUDIO_CHANNELS")
    audio_chunk_size: int = Field(default=1024, env="AUDIO_CHUNK_SIZE")
    vad_mode: int = Field(default=3, env="VAD_MODE")
    no_speech_threshold: float = Field(default=1.0, env="NO_SPEECH_THRESHOLD")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], 
        env="CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # File Storage
    audio_storage_path: str = Field(default="/app/storage/audio", env="AUDIO_STORAGE_PATH")
    max_audio_file_size_mb: int = Field(default=10, env="MAX_AUDIO_FILE_SIZE_MB")
    audio_retention_days: int = Field(default=30, env="AUDIO_RETENTION_DAYS")
    
    log_storage_path: str = Field(default="/app/storage/logs", env="LOG_STORAGE_PATH")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_retention_days: int = Field(default=90, env="LOG_RETENTION_DAYS")
    
    # Performance & Limits
    rate_limit_requests_per_minute: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst: int = Field(default=20, env="RATE_LIMIT_BURST")
    
    # WebSocket Configuration
    max_websocket_connections: int = Field(default=50, env="MAX_WEBSOCKET_CONNECTIONS")
    websocket_heartbeat_interval: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    websocket_timeout: int = Field(default=300, env="WEBSOCKET_TIMEOUT")
    
    # Cache Configuration
    cache_default_ttl_seconds: int = Field(default=900, env="CACHE_DEFAULT_TTL_SECONDS")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    cache_cleanup_interval: int = Field(default=3600, env="CACHE_CLEANUP_INTERVAL")
    
    # External Services
    news_api_key: Optional[str] = Field(default=None, env="NEWS_API_KEY")
    finnhub_api_key: Optional[str] = Field(default=None, env="FINNHUB_API_KEY")
    polygon_api_key: Optional[str] = Field(default=None, env="POLYGON_API_KEY")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    google_analytics_id: Optional[str] = Field(default=None, env="GOOGLE_ANALYTICS_ID")
    mixpanel_token: Optional[str] = Field(default=None, env="MIXPANEL_TOKEN")
    
    # Development
    reload: bool = Field(default=True, env="RELOAD")
    profiling: bool = Field(default=False, env="PROFILING")
    
    # Deployment
    render: bool = Field(default=False, env="RENDER")
    render_external_url: Optional[str] = Field(default=None, env="RENDER_EXTERNAL_URL")
    
    def is_database_configured(self) -> bool:
        """Check if database is properly configured."""
        return bool(self.supabase_url and self.supabase_key)
    
    def is_cache_configured(self) -> bool:
        """Check if cache is properly configured."""
        return bool(self.upstash_redis_rest_url and self.upstash_redis_rest_token)
    
    class Config:
        env_file = ["backend/.env", "env_files/supabase.env", "env_files/upstash.env", "env_files/render.env"]
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
