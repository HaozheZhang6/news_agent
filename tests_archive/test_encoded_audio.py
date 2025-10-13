#!/usr/bin/env python3
"""
Test WebSocket with encoded audio files
"""

import json
import asyncio
import websockets
import sys
from pathlib import Path

async def test_encoded_audio(file_path: str, ws_url: str = "ws://localhost:8000/ws/voice"):
    """Test sending encoded audio file via WebSocket"""
    
    # Load the encoded JSON file
    with open(file_path, 'r') as f:
        message = json.load(f)
    
    print(f"🎵 Testing encoded file: {Path(file_path).name}")
    print(f"📊 File size: {message['data']['file_size']:,} bytes")
    print(f"📊 Encoded size: {len(message['data']['audio_chunk']):,} chars")
    print(f"🎵 Format: {message['data']['format']}")
    print(f"🆔 Session ID: {message['data']['session_id']}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ Connected to {ws_url}")
            
            # Send the encoded message
            await websocket.send(json.dumps(message))
            print("📤 Audio message sent!")
            
            # Wait for responses
            print("⏳ Waiting for responses...")
            timeout_count = 0
            max_timeout = 10  # 10 seconds timeout
            
            while timeout_count < max_timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_data = json.loads(response)
                    print(f"📥 Response: {response_data.get('event', 'unknown')}")
                    
                    if response_data.get('event') == 'transcription':
                        print(f"🎤 Transcription: {response_data.get('data', {}).get('text', 'N/A')}")
                    elif response_data.get('event') == 'agent_response':
                        print(f"🤖 Agent: {response_data.get('data', {}).get('text', 'N/A')}")
                    elif response_data.get('event') == 'error':
                        print(f"❌ Error: {response_data.get('data', {}).get('message', 'N/A')}")
                        break
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⏰ Timeout {timeout_count}/{max_timeout}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_encoded_audio.py <encoded_json_file>")
        print("Example: python test_encoded_audio.py tests/voice_samples/encoded/test_news_nvda_latest_encoded.json")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    asyncio.run(test_encoded_audio(file_path))

if __name__ == "__main__":
    main()
