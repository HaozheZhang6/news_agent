#!/usr/bin/env python3
"""Test WebSocket connection to Voice News Agent backend."""

import asyncio
import json
import websockets
import sys

async def test_websocket(url: str):
    """Test WebSocket connection and send commands."""
    try:
        print(f"Connecting to {url}...")
        async with websockets.connect(url) as websocket:
            print("✅ Connected successfully!")
            
            # Send a test command
            test_message = {
                "type": "text_command",
                "command": "tell me the news",
                "user_id": "03f6b167-0c4d-4983-a380-54b8eb42f830",
                "session_id": "test-session-1"
            }
            
            print(f"📤 Sending: {json.dumps(test_message, indent=2)}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            # Send another command
            test_message2 = {
                "type": "text_command", 
                "command": "what about stock prices?",
                "user_id": "03f6b167-0c4d-4983-a380-54b8eb42f830",
                "session_id": "test-session-1"
            }
            
            print(f"📤 Sending: {json.dumps(test_message2, indent=2)}")
            await websocket.send(json.dumps(test_message2))
            
            response2 = await websocket.recv()
            print(f"📥 Received: {response2}")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Default to local backend
    url = "ws://localhost:8000/ws/voice"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "render":
            url = "wss://voice-news-agent-api.onrender.com/ws/voice"
        else:
            url = sys.argv[1]
    
    print(f"Testing WebSocket at: {url}")
    asyncio.run(test_websocket(url))
