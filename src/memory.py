import json
import os
from pathlib import Path

# Define the path for the memory file
MEMORY_FILE = Path(__file__).resolve().parent.parent / "user_preferences.json"

def load_preferences() -> dict:
    """Loads user preferences from a JSON file."""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {"preferred_topics": [], "watchlist_stocks": []}

def save_preferences(preferences: dict):
    """Saves user preferences to a JSON file."""
    with open(MEMORY_FILE, 'w') as f:
        json.dump(preferences, f, indent=4)
