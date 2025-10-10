"""Profile subservice: edit profile, preferences, and watchlist."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from ...database import get_database
from ...models.user import UserPreferencesUpdate


router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/{user_id}/preferences")
async def get_preferences(user_id: str, db=Depends(get_database)):
    prefs = await db.get_user_preferences(user_id)
    return prefs or {}


@router.put("/{user_id}/preferences")
async def update_preferences(user_id: str, update: UserPreferencesUpdate, db=Depends(get_database)):
    ok = await db.update_user_preferences(user_id, update.model_dump(exclude_none=True))
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update preferences")
    return {"status": "ok"}


@router.get("/{user_id}/watchlist")
async def get_watchlist(user_id: str, db=Depends(get_database)):
    prefs = await db.get_user_preferences(user_id)
    return {"watchlist": (prefs or {}).get("watchlist_stocks", [])}


@router.post("/{user_id}/watchlist/add")
async def add_to_watchlist(user_id: str, symbols: List[str], db=Depends(get_database)):
    prefs = await db.get_user_preferences(user_id) or {}
    current = set(prefs.get("watchlist_stocks", []))
    updated = sorted(current.union(set([s.upper() for s in symbols if s])))
    ok = await db.update_user_preferences(user_id, {"watchlist_stocks": updated})
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update watchlist")
    return {"status": "ok", "watchlist": updated}


@router.post("/{user_id}/watchlist/remove")
async def remove_from_watchlist(user_id: str, symbols: List[str], db=Depends(get_database)):
    prefs = await db.get_user_preferences(user_id) or {}
    current = set(prefs.get("watchlist_stocks", []))
    updated = sorted(current.difference(set([s.upper() for s in symbols if s])))
    ok = await db.update_user_preferences(user_id, {"watchlist_stocks": updated})
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update watchlist")
    return {"status": "ok", "watchlist": updated}

@router.post("/{user_id}/watchlist/set")
async def set_watchlist(user_id: str, symbols: List[str], db=Depends(get_database)):
    normalized = sorted({s.upper() for s in symbols if s})
    ok = await db.update_user_preferences(user_id, {"watchlist_stocks": normalized})
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to set watchlist")
    return {"status": "ok", "watchlist": normalized}


