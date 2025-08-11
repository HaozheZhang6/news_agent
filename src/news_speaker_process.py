"""News speaker thread for TTS output and content management."""
import threading
import time
import asyncio

async def handle_interrupt_command(command, ipc_manager, agent):
    """Handle immediate interrupt commands."""
    from . import voice_output
    from .ipc import CommandType
    
    ipc_manager.set_state('is_speaking', False)
    
    if command.type == CommandType.STOP:
        await voice_output.say("Stopped.", None)
        
    elif command.type == CommandType.DEEP_DIVE:
        current_index = ipc_manager.get_state('current_news_index')
        if current_index >= 0:
            deep_dive = agent.get_deep_dive(current_index)
            await voice_output.say(deep_dive, None)
        else:
            await voice_output.say("No news item to dive deeper into.", None)
            
    elif command.type == CommandType.SKIP:
        current_index = ipc_manager.get_state('current_news_index') 
        if current_index >= 0 and current_index + 1 < len(agent.current_news_items):
            next_index = current_index + 1
            ipc_manager.set_state('current_news_index', next_index)
            brief = await agent._rephrase_news_item(
                agent.current_news_items[next_index], "brief"
            )
            await voice_output.say(f"Next: {brief}", None)
        else:
            await voice_output.say("No more news to skip to.", None)

async def handle_content_command(command, ipc_manager, agent):
    """Handle content requests (news, stocks)."""
    from . import voice_output
    
    try:
        response = await agent.get_response(command.data)
        print(f"Response: {response}")
        # Update shared state
        if "news headlines" in response.lower():
            ipc_manager.set_state('current_news_index', 0)
            
        await voice_output.say(response, None)
        ipc_manager.set_state('is_speaking', False)
        
    except Exception as e:
        print(f"Error handling content: {e}")

async def news_speaker_worker_async(command_queue, interrupt_event, ipc_manager):
    """Async worker function for news speaker process."""
    from .agent import NewsAgent
    from .ipc import CommandType
    
    print("News speaker started...")
    agent = NewsAgent()
    
    while True:
        # Check for commands every 10ms for immediate response
        try:
            command = command_queue.get(timeout=0.01)
            
            print(f"Processing command: {command.type}")
            
            # Clear interrupt flag
            interrupt_event.clear()
            ipc_manager.set_state('interrupt_requested', False)
            
            # Handle command based on type
            if command.type in [CommandType.STOP, CommandType.DEEP_DIVE, CommandType.SKIP]:
                await handle_interrupt_command(command, ipc_manager, agent)
            else:
                await handle_content_command(command, ipc_manager, agent)
                
        except:
            # No command, small sleep to prevent busy waiting
            await asyncio.sleep(0.01)

def news_speaker_worker(command_queue, interrupt_event, ipc_manager):
    """Sync wrapper for async speaker worker."""
    asyncio.run(news_speaker_worker_async(command_queue, interrupt_event, ipc_manager))

def start_speaker_thread(ipc_manager):
    """Start the news speaker in a separate thread."""
    thread = threading.Thread(
        target=news_speaker_worker,
        args=(ipc_manager.command_queue, ipc_manager.interrupt_event, ipc_manager),
        daemon=True
    )
    thread.start()
    return thread