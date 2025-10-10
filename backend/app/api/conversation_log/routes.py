"""Conversation logging routes for sessions and messages."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from ...database import get_database
from ...models.conversation import ConversationMessageCreate, ConversationSessionCreate


router = APIRouter(prefix="/api/conversation", tags=["conversation-log"])


@router.post("/session/start")
async def start_session(payload: ConversationSessionCreate, db=Depends(get_database)):
    session = await db.create_conversation_session(payload.user_id)
    if not session:
        raise HTTPException(status_code=500, detail="Failed to create session")
    return session


@router.post("/message")
async def log_message(payload: ConversationMessageCreate, db=Depends(get_database)):
    # Map legacy message_type to 'role' column
    type_to_role = {
        "user_input": "user",
        "agent_response": "agent",
        "system_event": "system",
    }
    role = type_to_role.get(payload.message_type, "system")
    item = await db.add_conversation_message(
        session_id=payload.session_id,
        user_id=payload.user_id,
        role=role,
        content=payload.content,
        metadata={
            "audio_url": payload.audio_url,
            "processing_time_ms": payload.processing_time_ms,
            "confidence_score": payload.confidence_score,
            "referenced_news_ids": payload.referenced_news_ids,
            **(payload.metadata or {})
        }
    )
    if not item:
        raise HTTPException(status_code=500, detail="Failed to add message")
    return item


@router.get("/messages/{session_id}")
async def list_messages(session_id: str, limit: int = 50, db=Depends(get_database)):
    items = await db.get_conversation_messages(session_id, limit=limit)
    return {"messages": items}


