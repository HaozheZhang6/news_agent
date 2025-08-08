"""News speaker process for TTS output and content management."""
import multiprocessing as mp
import time
import asyncio

async def handle_interrupt_command(command, shared_state, agent):
    """Handle immediate interrupt commands."""
    from . import voice_output
    from .ipc import CommandType
    
    shared_state['is_speaking'] = False
    
    if command.type == CommandType.STOP:
        await voice_output.say("Stopped.", None)
        
    elif command.type == CommandType.DEEP_DIVE:
        current_index = shared_state['current_news_index']
        if current_index >= 0:
            deep_dive = agent.get_deep_dive(current_index)
            await voice_output.say(deep_dive, None)
        else:
            await voice_output.say("No news item to dive deeper into.", None)
            
    elif command.type == CommandType.SKIP:
        current_index = shared_state['current_news_index'] 
        if current_index >= 0 and current_index + 1 < len(agent.current_news_items):
            next_index = current_index + 1
            shared_state['current_news_index'] = next_index
            brief = await agent._rephrase_news_item(
                agent.current_news_items[next_index], "brief"
            )
            await voice_output.say(f"Next: {brief}", None)
        else:
            await voice_output.say("No more news to skip to.", None)

async def handle_content_command(command, shared_state, agent):
    """Handle content requests (news, stocks)."""
    from . import voice_output
    
    try:
        response = await agent.get_response(command.data)
        
        # Update shared state
        if "news headlines" in response.lower():
            shared_state['current_news_index'] = 0
            
        await voice_output.say(response, None)
        shared_state['is_speaking'] = False
        
    except Exception as e:
        print(f"Error handling content: {e}")

async def news_speaker_worker_async(command_queue, interrupt_event, shared_state):
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
            shared_state['interrupt_requested'] = False
            
            # Handle command based on type
            if command.type in [CommandType.STOP, CommandType.DEEP_DIVE, CommandType.SKIP]:
                await handle_interrupt_command(command, shared_state, agent)
            else:
                await handle_content_command(command, shared_state, agent)
                
        except:
            # No command, small sleep to prevent busy waiting
            await asyncio.sleep(0.01)

def news_speaker_worker(command_queue, interrupt_event, shared_state):
    """Sync wrapper for async speaker worker."""
    asyncio.run(news_speaker_worker_async(command_queue, interrupt_event, shared_state))

def start_speaker_process(ipc_manager):
    """Start the news speaker in a separate process.""" 
    process = mp.Process(
        target=news_speaker_worker,
        args=(ipc_manager.command_queue, ipc_manager.interrupt_event, ipc_manager.shared_state)
    )
    process.daemon = True
    process.start()
    return process