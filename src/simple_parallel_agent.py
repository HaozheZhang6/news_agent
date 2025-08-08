"""Simple, reliable parallel news agent with immediate interruption."""
import threading
import queue
import asyncio
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from . import voice_output
from .agent import NewsAgent


class CommandType(Enum):
    STOP = "stop"
    SKIP = "skip" 
    DEEP_DIVE = "deep_dive"
    NEWS_REQUEST = "news_request"
    EXIT = "exit"


@dataclass
class Command:
    type: CommandType
    text: str = ""
    timestamp: float = 0
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class VoiceListener:
    """Continuous voice listener with immediate command classification."""
    
    def __init__(self, command_queue: queue.Queue):
        self.command_queue = command_queue
        self.running = False
        self.thread = None
    
    def classify_command(self, text: str) -> Command:
        """Fast command classification - <1ms."""
        text_lower = text.lower().strip()
        
        # Immediate interrupt commands
        if any(word in text_lower for word in ["stop", "pause", "quiet"]):
            return Command(CommandType.STOP, text)
        
        if any(phrase in text_lower for phrase in ["tell me more", "dive deeper", "explain", "more about"]):
            return Command(CommandType.DEEP_DIVE, text)
        
        if "skip" in text_lower or "next" in text_lower:
            return Command(CommandType.SKIP, text)
        
        if any(word in text_lower for word in ["exit", "quit", "goodbye"]):
            return Command(CommandType.EXIT, text)
        
        # Default to news request
        return Command(CommandType.NEWS_REQUEST, text)
    
    def listen_loop(self):
        """Continuous listening loop.""" 
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        print("🎤 Voice listener started - say 'stop', 'tell me more', or 'skip'")
        
        # Adjust for ambient noise once
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        
        while self.running:
            try:
                # Listen for speech
                with microphone as source:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=8)
                
                # Quick recognition
                try:
                    text = recognizer.recognize_google(audio)
                    print(f"🎯 Heard: '{text}'")
                    
                    # Classify and queue immediately
                    command = self.classify_command(text)
                    self.command_queue.put(command)
                    
                except sr.UnknownValueError:
                    pass  # Ignore unclear speech
                    
            except sr.WaitTimeoutError:
                continue  # Keep listening
            except Exception as e:
                print(f"❌ Listener error: {e}")
                time.sleep(0.5)
    
    def start(self):
        """Start listener thread."""
        self.running = True
        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop listener thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)


class NewsSpeaker:
    """News speaker with immediate interruption capability."""
    
    def __init__(self):
        self.agent = NewsAgent()
        self.current_news_index = -1
        self.is_speaking = False
        self.current_task: Optional[asyncio.Task] = None
        self.interrupt_event = asyncio.Event()
    
    async def say_interruptible(self, text: str) -> bool:
        """Speak text with interruption support. Returns True if completed."""
        self.is_speaking = True
        self.interrupt_event.clear()
        
        try:
            self.current_task = asyncio.create_task(
                voice_output.say(text, self.interrupt_event)
            )
            await self.current_task
            return True
        except asyncio.CancelledError:
            return False
        finally:
            self.is_speaking = False
            self.current_task = None
    
    def interrupt_speech(self):
        """Immediately interrupt current speech."""
        if self.current_task and not self.current_task.done():
            self.interrupt_event.set()
            self.current_task.cancel()
    
    async def handle_stop(self, command: Command):
        """Handle STOP command."""
        self.interrupt_speech()
        await asyncio.sleep(0.05)  # Brief pause
        await self.say_interruptible("Stopped.")
    
    async def handle_deep_dive(self, command: Command):
        """Handle DEEP_DIVE command."""
        self.interrupt_speech()
        await asyncio.sleep(0.05)
        
        if self.current_news_index >= 0 and self.current_news_index < len(self.agent.current_news_items):
            deep_dive_text = self.agent.get_deep_dive(self.current_news_index)
            await self.say_interruptible(f"Here's more detail: {deep_dive_text}")
        else:
            await self.say_interruptible("I don't have a current news item to dive deeper into. Please ask for news first.")
    
    async def handle_skip(self, command: Command):
        """Handle SKIP command."""
        self.interrupt_speech()
        await asyncio.sleep(0.05)
        
        if self.current_news_index >= 0 and self.current_news_index + 1 < len(self.agent.current_news_items):
            self.current_news_index += 1
            next_item = self.agent.current_news_items[self.current_news_index]
            brief = await self.agent._rephrase_news_item(next_item, "brief")
            await self.say_interruptible(f"Next item: {brief}")
        else:
            await self.say_interruptible("No more news items to skip to.")
            self.current_news_index = -1
    
    async def handle_news_request(self, command: Command):
        """Handle news request.""" 
        self.interrupt_speech()
        await asyncio.sleep(0.05)
        
        try:
            response = await self.agent.get_response(command.text)
            
            # Set index if this was news
            if "news headlines" in response.lower() and self.agent.current_news_items:
                self.current_news_index = 0
            else:
                self.current_news_index = -1
                
            await self.say_interruptible(response)
        except Exception as e:
            await self.say_interruptible(f"Sorry, I encountered an error: {str(e)}")


class ParallelNewsAgent:
    """Main parallel news agent coordinator."""
    
    def __init__(self):
        self.command_queue = queue.Queue()
        self.listener = VoiceListener(self.command_queue)
        self.speaker = NewsSpeaker()
        self.running = False
    
    async def process_commands(self):
        """Process commands with 10ms responsiveness."""
        print("🔊 Speaker ready - processing commands...")
        
        await self.speaker.say_interruptible("Hello! I'm your news agent. You can say 'what's the news', 'tell me more', 'skip', or 'stop'.")
        
        while self.running:
            try:
                # Check for commands every 10ms
                command = self.command_queue.get(timeout=0.01)
                
                print(f"⚡ Processing: {command.type.value}")
                
                # Handle command by type
                if command.type == CommandType.STOP:
                    await self.speaker.handle_stop(command)
                    
                elif command.type == CommandType.DEEP_DIVE:
                    await self.speaker.handle_deep_dive(command)
                    
                elif command.type == CommandType.SKIP:
                    await self.speaker.handle_skip(command)
                    
                elif command.type == CommandType.NEWS_REQUEST:
                    await self.speaker.handle_news_request(command)
                    
                elif command.type == CommandType.EXIT:
                    await self.speaker.say_interruptible("Goodbye!")
                    self.running = False
                    
            except queue.Empty:
                # No commands, small sleep to prevent busy-waiting
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"❌ Command processing error: {e}")
                await asyncio.sleep(0.1)
    
    async def run(self):
        """Run the parallel news agent."""
        print("🚀 Starting parallel news agent...")
        self.running = True
        
        # Start voice listener
        self.listener.start()
        
        try:
            # Process commands
            await self.process_commands()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.running = False
            self.listener.stop()


async def main():
    """Main entry point."""
    agent = ParallelNewsAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())