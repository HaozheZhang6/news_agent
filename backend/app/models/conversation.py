"""Conversation-related Pydantic models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ConversationMessage(BaseModel):
    """Conversation message model."""
    id: str = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    message_type: str = Field(..., description="Message type (user_input/agent_response/system_event)")
    content: str = Field(..., description="Message content")
    audio_url: Optional[str] = Field(None, description="Audio file URL")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    referenced_news_ids: List[str] = Field(default=[], description="Referenced news article IDs")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    created_at: datetime = Field(..., description="Message timestamp")


class ConversationSession(BaseModel):
    """Conversation session model."""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    session_start: datetime = Field(..., description="Session start time")
    session_end: Optional[datetime] = Field(None, description="Session end time")
    total_interactions: int = Field(default=0, description="Total interactions")
    voice_interruptions: int = Field(default=0, description="Voice interruptions count")
    topics_discussed: List[str] = Field(default=[], description="Topics discussed")
    is_active: bool = Field(default=True, description="Session active status")
    messages: Optional[List[ConversationMessage]] = Field(None, description="Session messages")


class ConversationMessageCreate(BaseModel):
    """Conversation message creation model."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    message_type: str = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    audio_url: Optional[str] = Field(None, description="Audio file URL")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    referenced_news_ids: List[str] = Field(default=[], description="Referenced news article IDs")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class ConversationSessionCreate(BaseModel):
    """Conversation session creation model."""
    user_id: str = Field(..., description="User ID")


class ConversationHistoryRequest(BaseModel):
    """Conversation history request model."""
    session_id: Optional[str] = Field(None, description="Specific session ID")
    user_id: str = Field(..., description="User ID")
    limit: int = Field(default=50, description="Maximum messages")
    offset: int = Field(default=0, description="Messages offset")
    message_type: Optional[str] = Field(None, description="Filter by message type")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")


class ConversationHistoryResponse(BaseModel):
    """Conversation history response model."""
    messages: List[ConversationMessage] = Field(..., description="Conversation messages")
    total_count: int = Field(..., description="Total message count")
    session_id: Optional[str] = Field(None, description="Session ID")
    has_more: bool = Field(..., description="Has more messages")


class ConversationSummary(BaseModel):
    """Conversation summary model."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    total_messages: int = Field(..., description="Total messages")
    user_messages: int = Field(..., description="User messages count")
    agent_messages: int = Field(..., description="Agent messages count")
    topics_discussed: List[str] = Field(..., description="Topics discussed")
    key_insights: List[str] = Field(..., description="Key insights")
    session_duration_minutes: float = Field(..., description="Session duration")
    average_response_time_ms: float = Field(..., description="Average response time")
    interruption_count: int = Field(..., description="Interruption count")
    created_at: datetime = Field(..., description="Summary timestamp")


class ConversationContext(BaseModel):
    """Conversation context model."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    recent_messages: List[ConversationMessage] = Field(..., description="Recent messages")
    current_topics: List[str] = Field(..., description="Current topics")
    user_preferences: Dict[str, Any] = Field(..., description="User preferences")
    conversation_memory: Dict[str, Any] = Field(..., description="Conversation memory")
    last_news_items: List[str] = Field(default=[], description="Last discussed news items")
    last_stock_queries: List[str] = Field(default=[], description="Last stock queries")


class ConversationInsight(BaseModel):
    """Conversation insight model."""
    insight_type: str = Field(..., description="Insight type")
    content: str = Field(..., description="Insight content")
    confidence: float = Field(..., description="Insight confidence")
    relevance_score: float = Field(..., description="Relevance score")
    timestamp: datetime = Field(..., description="Insight timestamp")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class ConversationAnalytics(BaseModel):
    """Conversation analytics model."""
    user_id: str = Field(..., description="User ID")
    total_sessions: int = Field(default=0, description="Total sessions")
    total_messages: int = Field(default=0, description="Total messages")
    average_session_duration_minutes: float = Field(default=0.0, description="Average session duration")
    average_messages_per_session: float = Field(default=0.0, description="Average messages per session")
    most_discussed_topics: List[str] = Field(default=[], description="Most discussed topics")
    peak_usage_hours: List[int] = Field(default=[], description="Peak usage hours")
    interruption_rate: float = Field(default=0.0, description="Interruption rate")
    user_satisfaction_score: float = Field(default=0.0, description="User satisfaction score")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")
