from . import voice_input
from . import voice_output
from . import agent

def main_loop():
    """The main conversational loop for the CLI agent."""
    news_agent = agent.NewsAgent()
    voice_output.say("Hello! I'm your news agent. How can I help you?")

    while True:
        command = voice_input.listen_for_command()

        if command:
            if "exit" in command.lower() or "quit" in command.lower():
                voice_output.say("Goodbye!")
                break
            
            response = news_agent.get_response(command)
            print(f"Agent: {response}")
            voice_output.say(response)

if __name__ == "__main__":
    main_loop()
