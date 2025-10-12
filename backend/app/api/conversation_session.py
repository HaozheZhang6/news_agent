"""
Conversation Session API

API endpoints for retrieving conversation session data and logs.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from ..utils.conversation_logger import get_conversation_logger, SessionInfo, ConversationTurn

router = APIRouter(prefix="/api/conversation-sessions", tags=["conversation-sessions"])


class ConversationTurnResponse(BaseModel):
    """Response model for conversation turn."""
    session_id: str
    user_id: str
    timestamp: str
    transcription: str
    agent_response: str
    processing_time_ms: float
    audio_format: str
    audio_size_bytes: int
    tts_chunks_sent: int
    error: Optional[str] = None
    metadata: Optional[dict] = None


class SessionInfoResponse(BaseModel):
    """Response model for session info."""
    session_id: str
    user_id: str
    session_start: str
    session_end: Optional[str] = None
    turns: List[ConversationTurnResponse]
    total_turns: int
    total_interruptions: int


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    sensevoice_loaded: bool
    sensevoice_model_path: Optional[str] = None
    tts_engine: str
    agent_type: Optional[str] = None
    loading_time_ms: dict


@router.get("/sessions/{session_id}", response_model=SessionInfoResponse)
async def get_conversation_session(session_id: str):
    """
    Retrieve full conversation session data by session ID.

    Args:
        session_id: Unique session identifier

    Returns:
        Complete session information including all conversation turns

    Raises:
        404: Session not found
    """
    logger = get_conversation_logger()

    session_info = logger.get_session_info(session_id)

    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Convert to response model
    turns = [
        ConversationTurnResponse(
            session_id=turn.session_id,
            user_id=turn.user_id,
            timestamp=turn.timestamp,
            transcription=turn.transcription,
            agent_response=turn.agent_response,
            processing_time_ms=turn.processing_time_ms,
            audio_format=turn.audio_format,
            audio_size_bytes=turn.audio_size_bytes,
            tts_chunks_sent=turn.tts_chunks_sent,
            error=turn.error,
            metadata=turn.metadata
        )
        for turn in session_info.turns
    ]

    return SessionInfoResponse(
        session_id=session_info.session_id,
        user_id=session_info.user_id,
        session_start=session_info.session_start,
        session_end=session_info.session_end,
        turns=turns,
        total_turns=session_info.total_turns,
        total_interruptions=session_info.total_interruptions
    )


@router.get("/sessions", response_model=List[SessionInfoResponse])
async def list_conversation_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of sessions to return")
):
    """
    List recent conversation sessions.

    Args:
        user_id: Optional user ID filter
        limit: Maximum number of sessions to return

    Returns:
        List of session information
    """
    logger = get_conversation_logger()

    # Get active sessions
    active_sessions = list(logger.active_sessions.values())

    # Filter by user_id if provided
    if user_id:
        active_sessions = [s for s in active_sessions if s.user_id == user_id]

    # Limit results
    active_sessions = active_sessions[:limit]

    # Convert to response models
    responses = []
    for session_info in active_sessions:
        turns = [
            ConversationTurnResponse(
                session_id=turn.session_id,
                user_id=turn.user_id,
                timestamp=turn.timestamp,
                transcription=turn.transcription,
                agent_response=turn.agent_response,
                processing_time_ms=turn.processing_time_ms,
                audio_format=turn.audio_format,
                audio_size_bytes=turn.audio_size_bytes,
                tts_chunks_sent=turn.tts_chunks_sent,
                error=turn.error,
                metadata=turn.metadata
            )
            for turn in session_info.turns
        ]

        responses.append(SessionInfoResponse(
            session_id=session_info.session_id,
            user_id=session_info.user_id,
            session_start=session_info.session_start,
            session_end=session_info.session_end,
            turns=turns,
            total_turns=session_info.total_turns,
            total_interruptions=session_info.total_interruptions
        ))

    return responses


@router.get("/models/info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Get information about loaded models.

    Returns:
        Model loading information including which models are loaded and loading times
    """
    logger = get_conversation_logger()
    model_info = logger.get_model_info()

    return ModelInfoResponse(
        sensevoice_loaded=model_info.get("sensevoice_loaded", False),
        sensevoice_model_path=model_info.get("sensevoice_model_path"),
        tts_engine=model_info.get("tts_engine", "edge-tts"),
        agent_type=model_info.get("agent_type"),
        loading_time_ms=model_info.get("loading_time_ms", {})
    )


@router.delete("/sessions/{session_id}")
async def delete_conversation_session(session_id: str):
    """
    Delete a conversation session.

    Args:
        session_id: Session identifier

    Returns:
        Success message
    """
    logger = get_conversation_logger()

    # End session if active
    session_info = logger.end_session(session_id)

    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return {"message": f"Session {session_id} deleted successfully"}