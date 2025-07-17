import asyncio
import queue
from . import voice_input
from . import voice_output
from . import agent

async def main_loop():
    """The main conversational loop for the CLI agent."""
    news_agent = agent.NewsAgent()
    
    # Event for interrupting speech
    interrupt_event = asyncio.Event()

    # Queue for commands from the voice listener thread
    command_queue = queue.Queue()
    voice_listener = voice_input.VoiceListener(command_queue)
    voice_listener.start()

    try:
        await voice_output.say("Hello! I'm your news agent. How can I help you?", interrupt_event)

        current_news_index = -1 # To keep track of which news item is being discussed

        while True:
            try:
                command = command_queue.get_nowait()
                command_lower = command.lower()

                # Interrupt any ongoing speech immediately
                interrupt_event.set()
                await asyncio.sleep(0.1) # Give a moment for interruption to register
                interrupt_event.clear()

                if "exit" in command_lower or "quit" in command_lower:
                    await voice_output.say("Goodbye!", interrupt_event)
                    break
                elif "tell me more" in command_lower:
                    if current_news_index != -1 and current_news_index < len(news_agent.current_news_items):
                        deep_dive_text = news_agent.get_deep_dive(current_news_index)
                        await voice_output.say(deep_dive_text, interrupt_event)
                    else:
                        await voice_output.say("I don't have more details on a current news item. Please ask for news first.", interrupt_event)
                elif "skip" in command_lower:
                    current_news_index += 1
                    if current_news_index < len(news_agent.current_news_items):
                        brief = await news_agent._rephrase_news_item(news_agent.current_news_items[current_news_index], "brief")
                        await voice_output.say(f"Next news item: {brief}", interrupt_event)
                    else:
                        await voice_output.say("No more news items to skip to.", interrupt_event)
                        current_news_index = -1 # Reset
                else:
                    response = await news_agent.get_response(command)
                    print(f"Agent: {response}")
                    await voice_output.say(response, interrupt_event)
                    
                    # If the response was news, set the current_news_index to 0
                    # This is a heuristic and might need refinement based on actual LLM output
                    if "Here are the latest news headlines" in response and news_agent.current_news_items:
                        current_news_index = 0
                    else:
                        current_news_index = -1 # Reset if not news

            except queue.Empty:
                # No command from listener, continue main loop (e.g., for async tasks)
                await asyncio.sleep(0.1) # Prevent busy-waiting

    finally:
        voice_listener.stop()

if __name__ == "__main__":
    asyncio.run(main_loop())