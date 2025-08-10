import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

# Define the path for the memory file
MEMORY_FILE = Path(__file__).resolve().parent.parent / "user_preferences.json"

@dataclass
class ConversationContext:
    """Represents a piece of conversation context."""
    timestamp: float
    user_input: str
    agent_response: str
    news_items: List[Dict[str, Any]] = None
    current_topic: str = None
    deep_dive_target: int = None  # Index of news item for deep dive
    
    def __post_init__(self):
        if self.news_items is None:
            self.news_items = []

class ConversationMemory:
    """Enhanced memory system for contextual conversations."""
    
    def __init__(self, max_context_items: int = 10):
        self.max_context_items = max_context_items
        self.context_history: List[ConversationContext] = []
        self.current_news_items: List[Dict[str, Any]] = []
        self.current_topic: Optional[str] = None
        self.last_response_timestamp: float = 0
        
    def add_context(self, user_input: str, agent_response: str, 
                   news_items: List[Dict[str, Any]] = None, topic: str = None):
        """Add new conversation context."""
        context = ConversationContext(
            timestamp=time.time(),
            user_input=user_input,
            agent_response=agent_response,
            news_items=news_items or [],
            current_topic=topic
        )
        
        self.context_history.append(context)
        
        # Update current state
        if news_items:
            self.current_news_items = news_items
        if topic:
            self.current_topic = topic
            
        self.last_response_timestamp = context.timestamp
        
        # Trim history to max size
        if len(self.context_history) > self.max_context_items:
            self.context_history = self.context_history[-self.max_context_items:]
    
    def get_deep_dive_context(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Determine what the user wants to dive deeper into."""
        deep_dive_keywords = ["tell me more", "dive deeper", "explain", "elaborate", 
                             "expand", "more details", "go deeper", "that's deep"]
        
        # Check if user is asking for deep dive
        if not any(keyword in user_input.lower() for keyword in deep_dive_keywords):
            return None
            
        # Look for recent news context
        for context in reversed(self.context_history):
            if context.news_items and time.time() - context.timestamp < 300:  # 5 minutes
                # Try to identify which news item they're referring to
                news_item_index = self._identify_target_news_item(user_input, context.news_items)
                if news_item_index is not None:
                    return {
                        'news_item': context.news_items[news_item_index],
                        'topic': context.current_topic,
                        'index': news_item_index
                    }
                # Default to first news item if can't identify specific one
                return {
                    'news_item': context.news_items[0],
                    'topic': context.current_topic,
                    'index': 0
                }
        
        return None
    
    def _identify_target_news_item(self, user_input: str, news_items: List[Dict]) -> Optional[int]:
        """Try to identify which news item user is referring to."""
        user_lower = user_input.lower()
        
        # Look for keywords in news headlines
        for i, item in enumerate(news_items):
            headline = item.get('title', '').lower()
            summary = item.get('summary', '').lower()
            
            # Extract key terms from headline
            key_terms = self._extract_key_terms(headline)
            
            # Check if any key terms appear in user input
            for term in key_terms:
                if term in user_lower:
                    return i
                    
            # Also check summary if available
            if summary:
                summary_terms = self._extract_key_terms(summary)
                for term in summary_terms:
                    if term in user_lower:
                        return i
        
        return None
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text (company names, important words)."""
        # Simple extraction - could be enhanced with NLP
        words = text.lower().split()
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        key_terms = [word.strip('.,!?()[]{}"') for word in words 
                    if len(word) > 3 and word not in stop_words]
        return key_terms
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current conversation context."""
        return {
            'current_news_items': self.current_news_items,
            'current_topic': self.current_topic,
            'recent_context': self.context_history[-3:] if self.context_history else [],
            'last_response_time': self.last_response_timestamp
        }
    
    def clear_context(self):
        """Clear conversation context (but keep preferences)."""
        self.context_history.clear()
        self.current_news_items.clear()
        self.current_topic = None
        self.last_response_timestamp = 0

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

# Global conversation memory instance
conversation_memory = ConversationMemory()
