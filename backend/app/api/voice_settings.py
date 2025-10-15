"""
Voice Settings API

Endpoints for managing voice configuration (VAD, compression, TTS settings)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from ..models.voice import VoiceSettings
from ..database import get_database
from ..cache import get_cache

router = APIRouter(prefix="/api/voice-settings", tags=["voice-settings"])


@router.get("/{user_id}", response_model=VoiceSettings)
async def get_voice_settings(user_id: str):
    """
    Get voice settings for a user.

    Returns default settings if user hasn't customized them.
    """
    try:
        cache = await get_cache()

        # Try to get from cache first
        cache_key = f"voice_settings:{user_id}"
        cached_settings = await cache.get(cache_key)

        if cached_settings:
            return VoiceSettings.model_validate_json(cached_settings)

        # Try to get from database
        db = await get_database()
        settings_data = await db.get_voice_settings(user_id)

        if settings_data:
            settings = VoiceSettings(**settings_data)
        else:
            # Return defaults
            settings = VoiceSettings()

        # Cache for 1 hour
        await cache.set(cache_key, settings.model_dump_json(), ex=3600)

        return settings

    except Exception as e:
        # On error, return defaults
        print(f"Error getting voice settings: {e}")
        return VoiceSettings()


@router.put("/{user_id}", response_model=VoiceSettings)
async def update_voice_settings(
    user_id: str,
    settings: VoiceSettings
):
    """
    Update voice settings for a user.

    All settings are validated by the VoiceSettings model.
    """
    try:
        cache = await get_cache()
        db = await get_database()

        # Save to database
        settings_data = settings.model_dump()
        settings_data['user_id'] = user_id
        settings_data['updated_at'] = datetime.now().isoformat()

        await db.save_voice_settings(user_id, settings_data)

        # Update cache
        cache_key = f"voice_settings:{user_id}"
        await cache.set(cache_key, settings.model_dump_json(), ex=3600)

        return settings

    except Exception as e:
        print(f"Error updating voice settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update voice settings")


@router.delete("/{user_id}")
async def reset_voice_settings(user_id: str):
    """
    Reset voice settings to defaults for a user.
    """
    try:
        cache = await get_cache()
        db = await get_database()

        # Delete from database
        await db.delete_voice_settings(user_id)

        # Clear cache
        cache_key = f"voice_settings:{user_id}"
        await cache.delete(cache_key)

        return {"message": "Voice settings reset to defaults"}

    except Exception as e:
        print(f"Error resetting voice settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset voice settings")


@router.get("/{user_id}/presets", response_model=dict)
async def get_vad_presets():
    """
    Get VAD configuration presets.
    """
    return {
        "sensitive": {
            "vad_threshold": 0.01,
            "silence_timeout_ms": 500,
            "backend_vad_mode": 0,
            "backend_energy_threshold": 200.0,
            "description": "Very sensitive - picks up soft speech, may detect noise"
        },
        "balanced": {
            "vad_threshold": 0.02,
            "silence_timeout_ms": 700,
            "backend_vad_mode": 2,
            "backend_energy_threshold": 500.0,
            "description": "Balanced - good for most environments"
        },
        "strict": {
            "vad_threshold": 0.03,
            "silence_timeout_ms": 1000,
            "backend_vad_mode": 3,
            "backend_energy_threshold": 800.0,
            "description": "Strict - filters noise, requires clear speech"
        }
    }


@router.get("/{user_id}/compression-info", response_model=dict)
async def get_compression_info():
    """
    Get audio compression information and file size estimates.
    """
    return {
        "formats": {
            "wav": {
                "compression": False,
                "file_size_3s": "94 KB",
                "quality": "Lossless",
                "description": "Uncompressed PCM audio"
            },
            "opus": {
                "compression": True,
                "file_size_3s": "18 KB",
                "quality": "High (64 kbps)",
                "description": "Opus codec - optimized for speech",
                "compression_ratio": "5x smaller"
            }
        },
        "recommendations": {
            "slow_connection": "opus",
            "fast_connection": "wav",
            "mobile": "opus",
            "desktop": "wav"
        }
    }
