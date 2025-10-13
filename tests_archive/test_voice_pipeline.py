#!/usr/bin/env python3
"""
Test script to verify voice-to-voice functionality.
Sends a voice file to the backend and checks for proper response.
"""
import asyncio
import websockets
import json
import base64
import os
from pathlib import Path

async def test_voice_to_voice():
    """Test sending voice file and receiving audio response."""
    
    # Connect to WebSocket
    uri = "ws://localhost:8000/ws/voice"
    print(f"🔌 Connecting to {uri}")
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")
        
        # Send connection message
        connect_msg = {
            "event": "connect",
            "data": {
                "user_id": "test_user_123",
                "session_id": None
            }
        }
        await websocket.send(json.dumps(connect_msg))
        print("📤 Sent connection message")
        
        # Wait for connection confirmation
        response = await websocket.recv()
        connect_response = json.loads(response)
        print(f"📥 Received: {connect_response['event']}")
        
        if connect_response['event'] == 'connected':
            session_id = connect_response['data']['session_id']
            print(f"🎯 Session ID: {session_id}")
            
            # Test with a voice file
            test_file = "tests/voice_samples/test_price_aapl_today.wav"
            if not os.path.exists(test_file):
                print(f"❌ Test file not found: {test_file}")
                return
            
            print(f"🎤 Loading test file: {test_file}")
            
            # Read and encode audio file
            with open(test_file, 'rb') as f:
                audio_data = f.read()
            
            audio_base64 = base64.b64encode(audio_data).decode()
            print(f"📊 Audio file size: {len(audio_data)} bytes")
            
            # Send audio chunk
            audio_msg = {
                "event": "audio_chunk",
                "data": {
                    "audio_chunk": audio_base64,
                    "format": "wav",
                    "session_id": session_id
                }
            }
            
            print("📤 Sending audio chunk...")
            await websocket.send(json.dumps(audio_msg))
            
            # Listen for responses
            print("👂 Listening for responses...")
            response_count = 0
            audio_chunks_received = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    response_data = json.loads(response)
                    response_count += 1
                    
                    print(f"📥 Response #{response_count}: {response_data['event']}")
                    
                    if response_data['event'] == 'transcription':
                        print(f"🎤 Transcribed: '{response_data['data']['text']}'")
                    
                    elif response_data['event'] == 'agent_response':
                        print(f"🤖 Agent response: '{response_data['data']['text']}'")
                    
                    elif response_data['event'] == 'tts_chunk':
                        audio_chunks_received += 1
                        chunk_size = len(response_data['data']['audio_chunk'])
                        print(f"🔊 TTS chunk #{audio_chunks_received}: {chunk_size} bytes")
                    
                    elif response_data['event'] == 'streaming_complete':
                        print(f"✅ Streaming complete! Received {audio_chunks_received} audio chunks")
                        break
                    
                    elif response_data['event'] == 'error':
                        print(f"❌ Error: {response_data['data']['message']}")
                        break
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error receiving response: {e}")
                    break
            
            print(f"🎉 Test completed! Received {response_count} total responses")
            
        else:
            print(f"❌ Connection failed: {connect_response}")

if __name__ == "__main__":
    print("🚀 Starting voice-to-voice test...")
    asyncio.run(test_voice_to_voice())
