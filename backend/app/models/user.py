"""User-related Pydantic models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UserBase(BaseModel):
    """Base user model."""
    email: str = Field(..., description="User email address")
    subscription_tier: str = Field(default="free", description="Subscription tier")


class UserCreate(UserBase):
    """User creation model."""
    pass


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[str] = None
    subscription_tier: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class User(UserBase):
    """User model."""
    id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_active: datetime = Field(..., description="Last activity timestamp")
    preferences: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class UserPreferences(BaseModel):
    """User preferences model."""
    preferred_topics: List[str] = Field(default=[], description="Preferred news topics")
    watchlist_stocks: List[str] = Field(default=[], description="Stock watchlist")
    voice_settings: Dict[str, Any] = Field(
        default={
            "speech_rate": 1.0,
            "voice_type": "default",
            "interruption_sensitivity": 0.5,
            "auto_play": True
        },
        description="Voice interaction settings"
    )
    notification_settings: Dict[str, Any] = Field(
        default={
            "breaking_news": True,
            "stock_alerts": True,
            "daily_briefing": True,
            "email_notifications": False
        },
        description="Notification preferences"
    )


class UserPreferencesUpdate(BaseModel):
    """User preferences update model."""
    preferred_topics: Optional[List[str]] = None
    watchlist_stocks: Optional[List[str]] = None
    voice_settings: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserSession(BaseModel):
    """User session model."""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    session_start: datetime = Field(..., description="Session start time")
    session_end: Optional[datetime] = Field(None, description="Session end time")
    total_interactions: int = Field(default=0, description="Total interactions in session")
    voice_interruptions: int = Field(default=0, description="Voice interruptions count")
    topics_discussed: List[str] = Field(default=[], description="Topics discussed")
    is_active: bool = Field(default=True, description="Session active status")


class UserInteraction(BaseModel):
    """User interaction model."""
    id: str = Field(..., description="Interaction ID")
    user_id: str = Field(..., description="User ID")
    interaction_type: str = Field(..., description="Type of interaction")
    target_content: Optional[str] = Field(None, description="Target content")
    success: bool = Field(default=True, description="Interaction success")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    created_at: datetime = Field(..., description="Interaction timestamp")


class UserAnalytics(BaseModel):
    """User analytics model."""
    user_id: str = Field(..., description="User ID")
    total_interactions: int = Field(default=0, description="Total interactions")
    successful_interactions: int = Field(default=0, description="Successful interactions")
    average_response_time_ms: float = Field(default=0.0, description="Average response time")
    most_used_topics: List[str] = Field(default=[], description="Most used topics")
    most_used_commands: List[str] = Field(default=[], description="Most used commands")
    session_count: int = Field(default=0, description="Total sessions")
    total_session_time_minutes: float = Field(default=0.0, description="Total session time")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")
