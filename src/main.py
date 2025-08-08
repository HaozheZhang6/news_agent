"""Main entry point for parallel news agent processes."""
import time
import signal
import sys
from .ipc import IPCManager
from .voice_listener_process import start_listener_process
from .news_speaker_process import start_speaker_process

def main():
    """Start parallel listener and speaker processes."""
    print("Starting news agent with parallel processes...")
    
    # Initialize IPC
    ipc_manager = IPCManager()
    
    # Start both processes
    listener_process = start_listener_process(ipc_manager)
    speaker_process = start_speaker_process(ipc_manager)
    
    def signal_handler(sig, frame):
        print("\nShutting down...")
        listener_process.terminate()
        speaker_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("News agent running. Say 'stop' to interrupt, 'tell me more' to dive deeper.")
        print("Press Ctrl+C to exit.")
        
        # Keep main process alive
        while True:
            time.sleep(1)
            
            # Check if processes are alive
            if not listener_process.is_alive():
                print("Listener process died, restarting...")
                listener_process = start_listener_process(ipc_manager)
                
            if not speaker_process.is_alive():
                print("Speaker process died, restarting...")
                speaker_process = start_speaker_process(ipc_manager)
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        listener_process.terminate()
        speaker_process.terminate()

if __name__ == "__main__":
    main()