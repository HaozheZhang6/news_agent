#!/usr/bin/env python3
"""
Enhanced WebSocket Audio Test with Compression Analysis
"""

import json
import asyncio
import websockets
import sys
from pathlib import Path
import time

async def test_compressed_audio(file_path: str, ws_url: str = "ws://localhost:8000/ws/voice"):
    """Test sending compressed audio file via WebSocket with detailed analysis"""
    
    # Load the encoded JSON file
    with open(file_path, 'r') as f:
        message = json.load(f)
    
    print(f"🎵 Testing compressed audio: {Path(file_path).name}")
    print(f"📊 Compressed file size: {message['data']['file_size']:,} bytes")
    print(f"📊 Base64 encoded size: {len(message['data']['audio_chunk']):,} chars")
    print(f"🎵 Format: {message['data']['format']}")
    print(f"🆔 Session ID: {message['data']['session_id']}")
    print(f"👤 User ID: {message['data']['user_id']}")
    
    # Show compression info if available
    if message['data'].get('compression'):
        comp_info = message['data']['compression']
        print(f"🎵 Compression: {comp_info['codec'].upper()} @ {comp_info['bitrate']}")
        print(f"📈 Compression ratio: {comp_info['compression_ratio']:.1f}x")
        print(f"💾 Original size: {comp_info['original_size']:,} bytes")
        print(f"💾 Compressed size: {comp_info['compressed_size']:,} bytes")
        print(f"💾 Space saved: {((comp_info['original_size'] - comp_info['compressed_size']) / comp_info['original_size'] * 100):.1f}%")
    
    print(f"\n🔌 Connecting to {ws_url}...")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ Connected successfully!")
            
            # Wait for the connected message to get the actual session ID
            connected_response = await websocket.recv()
            connected_data = json.loads(connected_response)
            actual_session_id = connected_data.get('data', {}).get('session_id')
            
            if actual_session_id:
                print(f"🆔 Using actual session ID: {actual_session_id}")
                # Update the message with the correct session ID
                message['data']['session_id'] = actual_session_id
            else:
                print(f"⚠️ No session ID received, using original: {message['data']['session_id']}")
            
            # Wait a moment for session to be fully established
            await asyncio.sleep(0.5)
            
            # Send the encoded message
            start_time = time.time()
            await websocket.send(json.dumps(message))
            send_time = time.time() - start_time
            print(f"📤 Audio message sent in {send_time:.3f}s!")
            
            # Wait for responses with more detailed logging
            print(f"⏳ Waiting for backend responses...")
            timeout_count = 0
            max_timeout = 15  # Increased timeout
            response_count = 0
            
            while timeout_count < max_timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_data = json.loads(response)
                    response_count += 1
                    
                    print(f"📥 Response #{response_count}: {response_data.get('event', 'unknown')}")
                    
                    if response_data.get('event') == 'connected':
                        print(f"   ✅ Session established: {response_data.get('data', {}).get('session_id', 'N/A')}")
                    
                    elif response_data.get('event') == 'transcription':
                        transcription = response_data.get('data', {}).get('text', 'N/A')
                        print(f"   🎤 Transcription: {transcription}")
                    
                    elif response_data.get('event') == 'agent_response':
                        response_text = response_data.get('data', {}).get('text', 'N/A')
                        print(f"   🤖 Agent Response: {response_text}")
                    
                    elif response_data.get('event') == 'tts_chunk':
                        print(f"   🔊 TTS Audio chunk received")
                    
                    elif response_data.get('event') == 'streaming_complete':
                        print(f"   ✅ TTS streaming complete")
                        break
                    
                    elif response_data.get('event') == 'error':
                        error_msg = response_data.get('data', {}).get('message', 'N/A')
                        print(f"   ❌ Error: {error_msg}")
                        break
                    
                    elif response_data.get('event') == 'packet_interruption':
                        print(f"   🚨 Packet interruption detected")
                    
                    else:
                        print(f"   ⚠️ Unknown event: {response_data.get('event')}")
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    if timeout_count % 5 == 0:  # Show progress every 5 seconds
                        print(f"⏰ Still waiting... ({timeout_count}/{max_timeout}s)")
            
            total_time = time.time() - start_time
            print(f"\n📊 Test Summary:")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Responses received: {response_count}")
            print(f"   Transmission time: {send_time:.3f}s")
            
            if response_count == 0:
                print(f"   ⚠️ No responses received - backend may not be processing audio")
            elif response_count > 0:
                print(f"   ✅ Backend is processing compressed audio successfully!")
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_compressed_audio.py <compressed_json_file>")
        print("Example: python test_compressed_audio.py tests/voice_samples/encoded_compressed_opus/test_news_nvda_latest_compressed_opus.json")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    asyncio.run(test_compressed_audio(file_path))

if __name__ == "__main__":
    main()
