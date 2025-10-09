"""User API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from app.models.user import UserPreferences, UserPreferencesUpdate, UserAnalytics
from app.core.agent_wrapper import get_agent
from app.database import get_database
from app.cache import get_cache

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    user_id: str = Query(..., description="User ID"),
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Get user preferences."""
    try:
        # Get preferences from agent wrapper
        preferences = await agent.get_user_preferences(user_id)
        
        # Convert to UserPreferences model
        user_prefs = UserPreferences(
            preferred_topics=preferences.get("preferred_topics", []),
            watchlist_stocks=preferences.get("watchlist_stocks", []),
            voice_settings=preferences.get("voice_settings", {
                "speech_rate": 1.0,
                "voice_type": "default",
                "interruption_sensitivity": 0.5,
                "auto_play": True
            }),
            notification_settings=preferences.get("notification_settings", {
                "breaking_news": True,
                "stock_alerts": True,
                "daily_briefing": True,
                "email_notifications": False
            })
        )
        
        return user_prefs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user preferences: {str(e)}")


@router.put("/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferencesUpdate,
    agent=Depends(get_agent),
    db=Depends(get_database)
):
    """Update user preferences."""
    try:
        # Convert to dictionary
        prefs_dict = {}
        if preferences.preferred_topics is not None:
            prefs_dict["preferred_topics"] = preferences.preferred_topics
        if preferences.watchlist_stocks is not None:
            prefs_dict["watchlist_stocks"] = preferences.watchlist_stocks
        if preferences.voice_settings is not None:
            prefs_dict["voice_settings"] = preferences.voice_settings
        if preferences.notification_settings is not None:
            prefs_dict["notification_settings"] = preferences.notification_settings
        
        # Update preferences through agent wrapper
        success = await agent.update_user_preferences(user_id, prefs_dict)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update preferences")
        
        return {"message": "Preferences updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user preferences: {str(e)}")


@router.get("/topics")
async def get_user_topics(
    user_id: str = Query(..., description="User ID"),
    agent=Depends(get_agent)
):
    """Get user's preferred topics."""
    try:
        # Get preferences from agent wrapper
        preferences = await agent.get_user_preferences(user_id)
        
        return {
            "preferred_topics": preferences.get("preferred_topics", []),
            "available_topics": [
                "technology",
                "finance",
                "politics",
                "crypto",
                "energy",
                "healthcare",
                "automotive",
                "real_estate",
                "retail",
                "general"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user topics: {str(e)}")


@router.post("/topics/add")
async def add_user_topic(
    user_id: str,
    topic: str,
    agent=Depends(get_agent)
):
    """Add topic to user's preferences."""
    try:
        # Get current preferences
        preferences = await agent.get_user_preferences(user_id)
        current_topics = preferences.get("preferred_topics", [])
        
        # Add topic if not already present
        if topic not in current_topics:
            current_topics.append(topic)
            
            # Update preferences
            success = await agent.update_user_preferences(user_id, {
                "preferred_topics": current_topics
            })
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to add topic")
        
        return {"message": f"Topic '{topic}' added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding topic: {str(e)}")


@router.delete("/topics/{topic}")
async def remove_user_topic(
    user_id: str,
    topic: str,
    agent=Depends(get_agent)
):
    """Remove topic from user's preferences."""
    try:
        # Get current preferences
        preferences = await agent.get_user_preferences(user_id)
        current_topics = preferences.get("preferred_topics", [])
        
        # Remove topic if present
        if topic in current_topics:
            current_topics.remove(topic)
            
            # Update preferences
            success = await agent.update_user_preferences(user_id, {
                "preferred_topics": current_topics
            })
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to remove topic")
        
        return {"message": f"Topic '{topic}' removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing topic: {str(e)}")


@router.get("/watchlist")
async def get_user_watchlist(
    user_id: str = Query(..., description="User ID"),
    agent=Depends(get_agent)
):
    """Get user's stock watchlist."""
    try:
        # Get preferences from agent wrapper
        preferences = await agent.get_user_preferences(user_id)
        
        return {
            "watchlist_stocks": preferences.get("watchlist_stocks", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user watchlist: {str(e)}")


@router.post("/watchlist/add")
async def add_watchlist_stock(
    user_id: str,
    symbol: str,
    agent=Depends(get_agent)
):
    """Add stock to user's watchlist."""
    try:
        # Get current preferences
        preferences = await agent.get_user_preferences(user_id)
        current_stocks = preferences.get("watchlist_stocks", [])
        
        # Add stock if not already present
        symbol_upper = symbol.upper()
        if symbol_upper not in current_stocks:
            current_stocks.append(symbol_upper)
            
            # Update preferences
            success = await agent.update_user_preferences(user_id, {
                "watchlist_stocks": current_stocks
            })
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to add stock")
        
        return {"message": f"Stock '{symbol_upper}' added to watchlist"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding stock to watchlist: {str(e)}")


@router.delete("/watchlist/{symbol}")
async def remove_watchlist_stock(
    user_id: str,
    symbol: str,
    agent=Depends(get_agent)
):
    """Remove stock from user's watchlist."""
    try:
        # Get current preferences
        preferences = await agent.get_user_preferences(user_id)
        current_stocks = preferences.get("watchlist_stocks", [])
        
        # Remove stock if present
        symbol_upper = symbol.upper()
        if symbol_upper in current_stocks:
            current_stocks.remove(symbol_upper)
            
            # Update preferences
            success = await agent.update_user_preferences(user_id, {
                "watchlist_stocks": current_stocks
            })
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to remove stock")
        
        return {"message": f"Stock '{symbol_upper}' removed from watchlist"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing stock from watchlist: {str(e)}")


@router.get("/analytics", response_model=UserAnalytics)
async def get_user_analytics(
    user_id: str = Query(..., description="User ID"),
    db=Depends(get_database)
):
    """Get user analytics."""
    try:
        # This would need to be implemented in the database layer
        # For now, return mock data
        analytics = UserAnalytics(
            user_id=user_id,
            total_interactions=100,
            successful_interactions=95,
            average_response_time_ms=1200.0,
            most_used_topics=["technology", "finance"],
            most_used_commands=["tell me the news", "stock prices"],
            session_count=25,
            total_session_time_minutes=750.0,
            last_active="2024-01-01T00:00:00Z"
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user analytics: {str(e)}")


@router.get("/health")
async def user_health_check():
    """Health check for user services."""
    return {
        "status": "healthy",
        "services": {
            "database": "available",
            "cache": "available"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }
