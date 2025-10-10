"""Conversation API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from ..models.conversation import ConversationHistoryRequest, ConversationHistoryResponse, ConversationSession, ConversationMessage
from ..database import get_database
from ..cache import get_cache

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/sessions", response_model=List[ConversationSession])
async def get_conversation_sessions(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, description="Maximum number of sessions"),
    offset: int = Query(0, description="Sessions offset"),
    db=Depends(get_database)
):
    """Get user's conversation sessions."""
    try:
        # This would need to be implemented in the database layer
        # For now, return mock data
        sessions = [
            ConversationSession(
                id="session-1",
                user_id=user_id,
                session_start="2024-01-01T00:00:00Z",
                session_end="2024-01-01T01:00:00Z",
                total_interactions=10,
                voice_interruptions=2,
                topics_discussed=["technology", "finance"],
                is_active=False
            )
        ]
        
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation sessions: {str(e)}")


@router.get("/{session_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation_messages(
    session_id: str,
    limit: int = Query(50, description="Maximum number of messages"),
    offset: int = Query(0, description="Messages offset"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    db=Depends(get_database)
):
    """Get messages for a specific conversation session."""
    try:
        # Get messages from database
        messages = await db.get_conversation_messages(session_id, limit)
        
        # Filter by message type if requested
        if message_type:
            messages = [msg for msg in messages if msg.get("message_type") == message_type]
        
        return ConversationHistoryResponse(
            messages=messages,
            total_count=len(messages),
            session_id=session_id,
            has_more=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation messages: {str(e)}")


@router.post("/sessions")
async def create_conversation_session(
    user_id: str,
    db=Depends(get_database)
):
    """Create new conversation session."""
    try:
        # Create session in database
        session = await db.create_conversation_session(user_id)
        
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating conversation session: {str(e)}")


@router.post("/{session_id}/messages")
async def add_conversation_message(
    session_id: str,
    user_id: str,
    message_type: str,
    content: str,
    audio_url: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
    confidence_score: Optional[float] = None,
    referenced_news_ids: List[str] = [],
    metadata: Dict[str, Any] = {},
    db=Depends(get_database)
):
    """Add message to conversation session."""
    try:
        # Add message to database
        message = await db.add_conversation_message(
            session_id=session_id,
            user_id=user_id,
            message_type=message_type,
            content=content,
            metadata={
                "audio_url": audio_url,
                "processing_time_ms": processing_time_ms,
                "confidence_score": confidence_score,
                "referenced_news_ids": referenced_news_ids,
                **metadata
            }
        )
        
        if not message:
            raise HTTPException(status_code=500, detail="Failed to add message")
        
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding conversation message: {str(e)}")


@router.get("/{session_id}/summary")
async def get_conversation_summary(
    session_id: str,
    db=Depends(get_database)
):
    """Get conversation summary."""
    try:
        # Get messages for summary
        messages = await db.get_conversation_messages(session_id, 100)
        
        # Generate summary (mock for now)
        summary = {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len([m for m in messages if m.get("message_type") == "user_input"]),
            "agent_messages": len([m for m in messages if m.get("message_type") == "agent_response"]),
            "topics_discussed": ["technology", "finance"],
            "key_insights": ["User interested in tech news", "Asked about stock prices"],
            "session_duration_minutes": 30.0,
            "average_response_time_ms": 1200.0,
            "interruption_count": 2,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation summary: {str(e)}")


@router.get("/health")
async def conversation_health_check():
    """Health check for conversation services."""
    return {
        "status": "healthy",
        "services": {
            "database": "available",
            "cache": "available"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }
