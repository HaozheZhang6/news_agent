"""Inter-thread communication for listener and speaker threads."""
import queue
import threading
import time
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Optional, Any, List
import heapq

class CommandPriority(IntEnum):
    """Command priorities (lower number = higher priority)."""
    IMMEDIATE = 1      # stop, pause, cancel - interrupt everything
    REFINEMENT = 2     # actually, instead, no - cancel previous command  
    CONTEXTUAL = 3     # tell me more, dive deeper - depends on recent context
    NORMAL = 4         # regular requests
    EXPIRED = 5        # commands older than threshold

class CommandType(Enum):
    STOP = "stop"
    CONTINUE = "continue"
    SKIP = "skip"
    REPEAT = "repeat"
    DEEP_DIVE = "deep_dive" 
    NEWS_REQUEST = "news_request"
    STOCK_REQUEST = "stock_request"
    WEATHER_REQUEST = "weather_request"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    SPEED_UP = "speed_up"
    SPEED_DOWN = "speed_down"
    HELP = "help"
    SETTINGS = "settings"

@dataclass
class Command:
    type: CommandType
    data: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)
    priority: CommandPriority = CommandPriority.NORMAL
    original_text: str = ""
    
    def __post_init__(self):
        if self.priority == CommandPriority.NORMAL:
            self.priority = self._calculate_priority()
    
    def _calculate_priority(self) -> CommandPriority:
        """Calculate command priority based on type and content."""
        # Immediate interrupts
        if self.type == CommandType.STOP:
            return CommandPriority.IMMEDIATE
        
        # Contextual commands that depend on recent responses
        if self.type == CommandType.DEEP_DIVE:
            return CommandPriority.CONTEXTUAL
            
        # Check for refinement words in original text
        if self.original_text:
            refinement_words = ['actually', 'instead', 'no', 'wait', 'cancel that', 'nevermind']
            if any(word in self.original_text.lower() for word in refinement_words):
                return CommandPriority.REFINEMENT
        
        # Check if command is expired (older than 5 seconds)
        if time.time() - self.timestamp > 5.0:
            return CommandPriority.EXPIRED
            
        return CommandPriority.NORMAL
    
    def __lt__(self, other):
        """For priority queue comparison."""
        if isinstance(other, Command):
            return (self.priority.value, self.timestamp) < (other.priority.value, other.timestamp)
        return NotImplemented

class SmartPriorityQueue:
    """Smart priority queue that handles command priorities and expiry."""
    
    def __init__(self):
        self._queue = []
        self._lock = threading.RLock()
        self._pending_commands = []  # Track pending commands for refinement
    
    def put(self, command: Command):
        """Add command to priority queue."""
        with self._lock:
            # Handle refinement commands - cancel previous pending commands
            if command.priority == CommandPriority.REFINEMENT:
                self._cancel_pending_commands()
            
            # Add to pending list for refinement tracking
            if command.priority <= CommandPriority.NORMAL:
                self._pending_commands.append(command)
            
            heapq.heappush(self._queue, command)
    
    def get(self, timeout=0.01) -> Optional[Command]:
        """Get highest priority command."""
        with self._lock:
            if not self._queue:
                return None
                
            command = heapq.heappop(self._queue)
            
            # Remove from pending list
            if command in self._pending_commands:
                self._pending_commands.remove(command)
                
            return command
    
    def _cancel_pending_commands(self):
        """Cancel pending commands (for refinement)."""
        # Mark pending commands as cancelled by removing from queue
        self._queue = [cmd for cmd in self._queue if cmd not in self._pending_commands]
        heapq.heapify(self._queue)
        self._pending_commands.clear()
    
    def size(self) -> int:
        """Get queue size."""
        with self._lock:
            return len(self._queue)

class IPCManager:
    def __init__(self):
        # Smart priority command queue
        self.command_queue = SmartPriorityQueue()
        
        # Shared state between threads (thread-safe with lock)
        self._state_lock = threading.RLock()
        self.shared_state = {
            'current_news_index': -1,
            'is_speaking': False,
            'current_topic': None,
            'interrupt_requested': False
        }
        
        # Interrupt event for immediate stopping
        self.interrupt_event = threading.Event()
        
    def get_state(self, key: str, default=None):
        """Thread-safe state getter."""
        with self._state_lock:
            return self.shared_state.get(key, default)
            
    def set_state(self, key: str, value):
        """Thread-safe state setter."""
        with self._state_lock:
            self.shared_state[key] = value
        
    def send_command(self, command: Command):
        """Send high-priority command from listener to speaker."""
        self.command_queue.put(command)
        
        # Set interrupt flag for immediate response
        if command.type in [CommandType.STOP, CommandType.DEEP_DIVE]:
            self.interrupt_event.set()
            self.set_state('interrupt_requested', True)
    
    def get_command(self, timeout=0.01) -> Optional[Command]:
        """Get command with 10ms timeout for immediate response."""
        try:
            return self.command_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def clear_interrupt(self):
        """Clear interrupt flags after handling."""
        self.interrupt_event.clear()
        self.set_state('interrupt_requested', False)
        
    def is_interrupted(self) -> bool:
        """Check if immediate interruption is requested."""
        return self.interrupt_event.is_set()