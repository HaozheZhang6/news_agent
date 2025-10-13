#!/usr/bin/env python3
"""Test audio WebSocket pipeline end-to-end."""
import asyncio
import websockets
import json
import base64
import sys
from pathlib import Path


async def test_audio_pipeline(audio_file: str):
    """Test complete audio pipeline: send audio → get TTS back."""
    
    print("=" * 80)
    print("🎤 AUDIO WEBSOCKET PIPELINE TEST")
    print("=" * 80)
    
    # Read audio file
    audio_path = Path(audio_file)
    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False
    
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()
    
    audio_b64 = base64.b64encode(audio_bytes).decode()
    print(f"📁 Loaded: {audio_path.name} ({len(audio_bytes)} bytes)")
    
    # Connect to WebSocket
    uri = "ws://localhost:8000/ws/voice/simple?user_id=test-pipeline"
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Wait for 'connected' event
            message = await websocket.recv()
            data = json.loads(message)
            if data['event'] == 'connected':
                session_id = data['data']['session_id']
                print(f"🎯 Session ID: {session_id[:8]}...")
            
            # Send audio chunk
            print(f"📤 Sending audio ({len(audio_b64)} bytes base64)...")
            audio_message = {
                "event": "audio_chunk",
                "data": {
                    "audio_chunk": audio_b64,
                    "format": "wav",
                    "sample_rate": 16000
                }
            }
            await websocket.send(json.dumps(audio_message))
            print("✅ Audio sent!")
            
            # Wait for responses
            transcription = None
            agent_response = None
            tts_chunks = []
            
            print("\n⏳ Waiting for responses...")
            print("-" * 80)
            
            # Wait for responses with simple loop
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                event = data['event']
                
                if event == 'transcription':
                    transcription = data['data']['text']
                    print(f"📝 TRANSCRIPTION: '{transcription}'")
                    
                elif event == 'agent_response':
                    agent_response = data['data']['text']
                    print(f"💬 AGENT RESPONSE: '{agent_response}'")
                    
                elif event == 'tts_chunk':
                    chunk_index = data['data']['chunk_index']
                    chunk_data = data['data']['audio_chunk']
                    tts_chunks.append(chunk_data)
                    print(f"🔊 TTS CHUNK #{chunk_index} ({len(chunk_data)} bytes)")
                    
                elif event == 'streaming_complete':
                    total_chunks = data['data']['total_chunks']
                    print(f"🎉 STREAMING COMPLETE! Total chunks: {total_chunks}")
                    break
                    
                elif event == 'error':
                    print(f"❌ ERROR: {data['data']}")
                    return False
            
            # Summary
            print("-" * 80)
            print("\n📊 PIPELINE SUMMARY:")
            print(f"✅ Transcription: {transcription is not None}")
            print(f"✅ Agent Response: {agent_response is not None}")
            print(f"✅ TTS Chunks: {len(tts_chunks)}")
            
            success = (
                transcription is not None and 
                agent_response is not None and 
                len(tts_chunks) > 0
            )
            
            if success:
                print("\n🎉 ✅ SUCCESS! Full audio pipeline working!")
                print(f"\n📝 User said: \"{transcription}\"")
                print(f"💬 Agent said: \"{agent_response}\"")
                print(f"🔊 Sent {len(tts_chunks)} audio chunks back")
            else:
                print("\n❌ FAILED! Pipeline incomplete")
            
            print("=" * 80)
            return success
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Default to first test audio file
    audio_file = "tests/voice_samples/test_price_msft_today.wav"
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    
    success = asyncio.run(test_audio_pipeline(audio_file))
    sys.exit(0 if success else 1)

