"""Main entry point for parallel news agent threads."""
import time
import signal
import sys
import threading
from .ipc import IPCManager
from .voice_listener_process import start_listener_thread
from .news_speaker_process import start_speaker_thread

def main():
    """Start parallel listener and speaker threads."""
    print("Starting news agent with parallel threads...")
    
    # Initialize IPC
    ipc_manager = IPCManager()
    
    # Start both threads
    listener_thread = start_listener_thread(ipc_manager)
    speaker_thread = start_speaker_thread(ipc_manager)
    
    def signal_handler(sig, frame):
        print("\nShutting down...")
        # Threads will exit when main thread exits
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("News agent running. Say 'stop' to interrupt, 'tell me more' to dive deeper.")
        print("Press Ctrl+C to exit.")
        
        # Keep main process alive
        while True:
            time.sleep(1)
            
            # Check if threads are alive
            if not listener_thread.is_alive():
                print("Listener thread died, restarting...")
                listener_thread = start_listener_thread(ipc_manager)
                
            if not speaker_thread.is_alive():
                print("Speaker thread died, restarting...")
                speaker_thread = start_speaker_thread(ipc_manager)
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Threads will be cleaned up automatically when main exits
        pass

if __name__ == "__main__":
    main()