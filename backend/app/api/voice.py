"""Voice API endpoints for text and voice commands."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from ..models.voice import VoiceCommandRequest, VoiceCommandResponse, VoiceSynthesis, VoiceSynthesisResponse
from ..core.agent_wrapper import get_agent
from ..database import get_database
from ..cache import get_cache

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command(
    request: VoiceCommandRequest,
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Process voice command (text input for iOS ASR integration)."""
    try:
        # Process the command through the agent
        result = await agent.process_voice_command(
            command=request.command,
            user_id=request.user_id,
            session_id=request.session_id,
            audio_url=None  # No audio URL for text input
        )
        
        return VoiceCommandResponse(
            response_text=result["response_text"],
            audio_url=result.get("audio_url"),
            response_type=result["response_type"],
            processing_time_ms=result["processing_time_ms"],
            session_id=request.session_id,
            news_items=result.get("news_items"),
            stock_data=result.get("stock_data"),
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice command: {str(e)}")


@router.post("/text-command", response_model=VoiceCommandResponse)
async def process_text_command(
    command: str,
    user_id: str,
    session_id: str,
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Process text command (alternative endpoint for text input)."""
    try:
        # Process the command through the agent
        result = await agent.process_text_command(
            command=command,
            user_id=user_id,
            session_id=session_id
        )
        
        return VoiceCommandResponse(
            response_text=result["response_text"],
            audio_url=result.get("audio_url"),
            response_type=result["response_type"],
            processing_time_ms=result["processing_time_ms"],
            session_id=session_id,
            news_items=result.get("news_items"),
            stock_data=result.get("stock_data"),
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text command: {str(e)}")


@router.post("/synthesize", response_model=VoiceSynthesisResponse)
async def synthesize_speech(
    request: VoiceSynthesis,
    agent=Depends(get_agent)
):
    """Synthesize text to speech."""
    try:
        # For now, return a mock response
        # In a full implementation, you would use Edge-TTS or similar
        
        return VoiceSynthesisResponse(
            audio_url=f"https://example.com/audio/{hash(request.text)}.mp3",
            audio_duration_ms=len(request.text) * 50,  # Rough estimate
            processing_time_ms=500,
            text_length=len(request.text),
            voice=request.voice,
            timestamp=request.timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {str(e)}")


@router.get("/health")
async def voice_health_check():
    """Health check for voice services."""
    return {
        "status": "healthy",
        "services": {
            "agent": "available",
            "tts": "available",
            "asr": "available"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }
