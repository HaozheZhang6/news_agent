"""Parallel news agent using threading for immediate responsiveness."""
import threading
import queue
import time
import asyncio
from . import voice_input
from . import voice_output
from . import agent
from .ipc import Command, CommandType

class ParallelNewsAgent:
    def __init__(self):
        self.agent = agent.NewsAgent()
        self.command_queue = queue.Queue()
        self.interrupt_event = threading.Event()
        self.current_news_index = -1
        self.is_speaking = False
        self.current_speech_task = None
        
    def classify_intent(self, text: str) -> Command:
        """Fast intent classification for immediate commands."""
        text_lower = text.lower()
        
        # Immediate interrupt commands  
        if any(word in text_lower for word in ["stop", "pause", "quiet"]):
            return Command(CommandType.STOP)
        
        if any(phrase in text_lower for phrase in ["tell me more", "dive deeper", "explain"]):
            return Command(CommandType.DEEP_DIVE)
            
        if "skip" in text_lower:
            return Command(CommandType.SKIP)
            
        # Content requests
        if any(word in text_lower for word in ["news", "headlines", "latest"]):
            return Command(CommandType.NEWS_REQUEST, data=text)
            
        if any(word in text_lower for word in ["stock", "price", "ticker"]):
            return Command(CommandType.STOCK_REQUEST, data=text)
            
        return Command(CommandType.NEWS_REQUEST, data=text)
    
    def voice_listener_thread(self):
        """Continuous voice listening thread - 10ms response time."""
        print("Voice listener thread started...")
        
        # Use existing voice_input module
        voice_listener = voice_input.VoiceListener(self.command_queue)
        voice_listener.start()
        
        while True:
            try:
                # Get raw command from voice_input 
                raw_command = self.command_queue.get(timeout=0.01)
                
                # Classify intent and create structured command
                command = self.classify_intent(raw_command)
                
                # Set interrupt for immediate commands
                if command.type in [CommandType.STOP, CommandType.DEEP_DIVE]:
                    self.interrupt_event.set()
                    
                # Put structured command back for speaker
                self.command_queue.put(command)
                print(f"Classified: {raw_command} -> {command.type}")
                
            except queue.Empty:
                time.sleep(0.01)  # 10ms polling
            except Exception as e:
                print(f"Listener error: {e}")
                time.sleep(0.1)
    
    async def handle_interrupt_command(self, command: Command):
        """Handle immediate interrupt commands."""
        # Cancel current speech immediately
        if self.current_speech_task:
            self.current_speech_task.cancel()
            self.current_speech_task = None
            
        self.is_speaking = False
        
        if command.type == CommandType.STOP:
            await voice_output.say("Stopped.", None)
            
        elif command.type == CommandType.DEEP_DIVE:
            if self.current_news_index >= 0:
                deep_dive = self.agent.get_deep_dive(self.current_news_index)
                self.current_speech_task = asyncio.create_task(
                    voice_output.say(deep_dive, self.interrupt_event)
                )
                self.is_speaking = True
            else:
                await voice_output.say("No news item to dive deeper into.", None)
                
        elif command.type == CommandType.SKIP:
            if (self.current_news_index >= 0 and 
                self.current_news_index + 1 < len(self.agent.current_news_items)):
                
                self.current_news_index += 1
                brief = await self.agent._rephrase_news_item(
                    self.agent.current_news_items[self.current_news_index], "brief"
                )
                self.current_speech_task = asyncio.create_task(
                    voice_output.say(f"Next: {brief}", self.interrupt_event)
                )
                self.is_speaking = True
            else:
                await voice_output.say("No more news to skip to.", None)
                self.current_news_index = -1
    
    async def handle_content_command(self, command: Command):
        """Handle content requests (news, stocks)."""
        try:
            response = await self.agent.get_response(command.data)
            
            # Update state
            if "news headlines" in response.lower():
                self.current_news_index = 0
            else:
                self.current_news_index = -1
                
            self.current_speech_task = asyncio.create_task(
                voice_output.say(response, self.interrupt_event)
            )
            self.is_speaking = True
            
            # Wait for completion or interruption
            try:
                await self.current_speech_task
            except asyncio.CancelledError:
                pass
            finally:
                self.is_speaking = False
                
        except Exception as e:
            print(f"Error handling content: {e}")
    
    async def speaker_loop(self):
        """Main speaker loop - processes commands with 10ms responsiveness."""
        print("Speaker loop started...")
        
        await voice_output.say("Hello! I'm your news agent. How can I help you?", None)
        
        while True:
            # Check for commands every 10ms
            try:
                command = self.command_queue.get(timeout=0.01)
                
                # Skip raw string commands (they get reprocessed by listener)
                if isinstance(command, str):
                    continue
                    
                print(f"Processing: {command.type}")
                
                # Clear interrupt flag
                self.interrupt_event.clear()
                
                # Handle based on command type
                if command.type in [CommandType.STOP, CommandType.DEEP_DIVE, CommandType.SKIP]:
                    await self.handle_interrupt_command(command)
                else:
                    await self.handle_content_command(command)
                    
            except queue.Empty:
                await asyncio.sleep(0.01)  # 10ms polling
            except Exception as e:
                print(f"Speaker error: {e}")
                await asyncio.sleep(0.1)
    
    async def run(self):
        """Run both listener and speaker concurrently."""
        # Start listener thread
        listener_thread = threading.Thread(target=self.voice_listener_thread, daemon=True)
        listener_thread.start()
        
        # Run speaker loop
        await self.speaker_loop()

async def main():
    """Main entry point."""
    agent = ParallelNewsAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())