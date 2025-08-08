"""Inter-process communication for listener and speaker processes."""
import multiprocessing as mp
import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any

class CommandType(Enum):
    STOP = "stop"
    SKIP = "skip"
    DEEP_DIVE = "deep_dive" 
    NEWS_REQUEST = "news_request"
    STOCK_REQUEST = "stock_request"

@dataclass
class Command:
    type: CommandType
    data: Optional[Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class IPCManager:
    def __init__(self):
        # High-priority command queue (10ms polling)
        self.command_queue = mp.Queue()
        
        # Shared state between processes
        self.shared_state = mp.Manager().dict({
            'current_news_index': -1,
            'is_speaking': False,
            'current_topic': None,
            'interrupt_requested': False
        })
        
        # Interrupt event for immediate stopping
        self.interrupt_event = mp.Event()
        
    def send_command(self, command: Command):
        """Send high-priority command from listener to speaker."""
        self.command_queue.put(command)
        
        # Set interrupt flag for immediate response
        if command.type in [CommandType.STOP, CommandType.DEEP_DIVE]:
            self.interrupt_event.set()
            self.shared_state['interrupt_requested'] = True
    
    def get_command(self, timeout=0.01) -> Optional[Command]:
        """Get command with 10ms timeout for immediate response."""
        try:
            return self.command_queue.get(timeout=timeout)
        except:
            return None
    
    def clear_interrupt(self):
        """Clear interrupt flags after handling."""
        self.interrupt_event.clear()
        self.shared_state['interrupt_requested'] = False
        
    def is_interrupted(self) -> bool:
        """Check if immediate interruption is requested."""
        return self.interrupt_event.is_set()