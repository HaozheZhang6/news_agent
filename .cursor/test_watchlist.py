#!/usr/bin/env python3
"""Test watchlist fetching from database directly."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_watchlist():
    """Test watchlist fetching."""
    from backend.app.database import get_database
    
    print("🧪 Testing Watchlist Fetching\n")
    
    # Initialize database
    db = await get_database()
    print("✅ Database initialized")
    
    # Test user ID
    user_id = "03f6b167-0c4d-4983-a380-54b8eb42f830"
    
    # Get preferences
    print(f"\n📋 Fetching preferences for user: {user_id[:8]}...")
    prefs = await db.get_user_preferences(user_id)
    
    if prefs:
        print(f"\n✅ Preferences returned:")
        for key, value in prefs.items():
            print(f"  - {key:20s}: {value}")
        
        watchlist = prefs.get("watchlist_stocks", [])
        print(f"\n📈 Watchlist stocks: {watchlist}")
        
        if watchlist:
            print(f"✅ SUCCESS! Found {len(watchlist)} stocks in watchlist")
        else:
            print("❌ FAILED! Watchlist is empty")
    else:
        print("❌ FAILED! No preferences returned")

if __name__ == "__main__":
    asyncio.run(test_watchlist())

