#!/usr/bin/env python3
"""
Simple WebSocket Test Script for Voice News Agent

This script demonstrates how to test the WebSocket interface from the terminal.
It sends a compressed audio file and receives the complete response pipeline.

Usage:
    python test_websocket_simple.py [audio_file.json]

Examples:
    python test_websocket_simple.py tests/voice_samples/encoded_compressed_opus/test_price_aapl_today_compressed_opus.json
    python test_websocket_simple.py tests/voice_samples/encoded_compressed_webm/test_followup_2_compressed_webm.json
"""

import asyncio
import json
import time
import sys
from pathlib import Path

try:
    import websockets
except ImportError:
    print("❌ websockets package not found. Install with: uv pip install websockets")
    sys.exit(1)


async def test_websocket_audio(audio_file_path: str):
    """Test WebSocket audio pipeline with compressed audio."""
    
    # Load the audio file
    try:
        with open(audio_file_path, 'r') as f:
            message = json.load(f)
    except FileNotFoundError:
        print(f"❌ Audio file not found: {audio_file_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in audio file: {e}")
        return
    
    # Extract audio information
    audio_data = message['data']
    audio_size = len(audio_data['audio_chunk'])
    format = audio_data.get('format', 'unknown')
    compression_info = audio_data.get('compression', {})
    
    print(f"🎵 Testing WebSocket Audio Pipeline")
    print(f"📁 File: {Path(audio_file_path).name}")
    print(f"📊 Audio size: {audio_size:,} chars (base64)")
    print(f"🎵 Format: {format}")
    
    if compression_info:
        print(f"🎵 Compression: {compression_info.get('codec', 'unknown').upper()} @ {compression_info.get('bitrate', 'unknown')}")
        print(f"📈 Compression ratio: {compression_info.get('compression_ratio', 0):.1f}x")
        print(f"💾 Original size: {compression_info.get('original_size', 0):,} bytes")
        print(f"💾 Compressed size: {compression_info.get('compressed_size', 0):,} bytes")
        print(f"💾 Space saved: {((compression_info.get('original_size', 0) - compression_info.get('compressed_size', 0)) / compression_info.get('original_size', 1) * 100):.1f}%")
    
    # WebSocket connection - try local first, then deployed
    ws_urls = [
        "ws://localhost:8000/ws/voice",
        "wss://voice-news-agent-api.onrender.com/ws/voice"
    ]
    
    for ws_url in ws_urls:
        print(f"\n🔌 Trying {ws_url}...")
        try:
            async with websockets.connect(ws_url) as websocket:
                print(f"✅ Connected successfully!")
                
                # Wait for the connected message to get the actual session ID
                try:
                    connected_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    connected_data = json.loads(connected_response)
                    actual_session_id = connected_data.get('data', {}).get('session_id')
                    
                    if actual_session_id:
                        print(f"🆔 Using actual session ID: {actual_session_id}")
                        # Update the message with the correct session ID
                        message['data']['session_id'] = actual_session_id
                    else:
                        print(f"⚠️ No session ID received, using original: {message['data']['session_id']}")
                except asyncio.TimeoutError:
                    print(f"⚠️ No connected message received, using original session ID")
                
                # Wait a moment for session to be fully established
                await asyncio.sleep(0.5)
                
                # Send the encoded message
                start_time = time.time()
                await websocket.send(json.dumps(message))
                send_time = time.time() - start_time
                print(f"📤 Audio message sent in {send_time:.3f}s!")
                
                # Wait for responses
                print(f"⏳ Waiting for backend responses...")
                timeout_count = 0
                max_timeout = 15
                response_count = 0
                
                try:
                    while timeout_count < max_timeout:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            response_data = json.loads(response)
                            response_count += 1
                            
                            event = response_data.get('event', 'unknown')
                            data = response_data.get('data', {})
                            
                            print(f"📥 Response #{response_count}: {event}")
                            
                            if event == 'connected':
                                print(f"   ✅ Session established: {data.get('session_id', 'unknown')}")
                            
                            elif event == 'transcription':
                                print(f"   🎤 Transcription: {data.get('text', 'No text')}")
                            
                            elif event == 'agent_response':
                                print(f"   🤖 Agent Response: {data.get('text', 'No response')}")
                            
                            elif event == 'tts_chunk':
                                chunk_index = data.get('chunk_index', 0)
                                print(f"   🔊 TTS Audio chunk #{chunk_index} received")
                            
                            elif event == 'streaming_complete':
                                print(f"   ✅ TTS streaming complete")
                                break
                            
                            elif event == 'streaming_interrupted':
                                print(f"   🛑 TTS streaming interrupted")
                                break
                            
                            elif event == 'error':
                                print(f"   ❌ Error: {data.get('message', 'Unknown error')}")
                                break
                            
                            else:
                                print(f"   ⚠️ Unknown event: {event}")
                            
                            timeout_count = 0  # Reset timeout counter
                            
                        except asyncio.TimeoutError:
                            timeout_count += 1
                            if timeout_count % 5 == 0:
                                print(f"⏰ Still waiting... ({timeout_count}/{max_timeout}s)")
                            
                except Exception as e:
                    print(f"❌ Error receiving responses: {e}")
                
                # Summary
                print(f"\n📊 Test Summary:")
                print(f"   Total time: {time.time() - start_time:.2f}s")
                print(f"   Responses received: {response_count}")
                print(f"   Transmission time: {send_time:.3f}s")
                
                if response_count > 1:
                    print(f"   ✅ Backend is processing compressed audio successfully!")
                else:
                    print(f"   ⚠️ Backend may not be processing audio correctly")
                
                return  # Success, exit the function
                
        except ConnectionRefusedError:
            print(f"❌ Connection refused to {ws_url}")
            continue
        except Exception as e:
            print(f"❌ Connection error to {ws_url}: {e}")
            continue
    
    print(f"❌ Failed to connect to any WebSocket URL")
    print(f"   Make sure the backend is running with: make run-server")


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python test_websocket_simple.py <audio_file.json>")
        print("\nAvailable test files:")
        
        # List available test files
        test_dirs = [
            "tests/voice_samples/encoded_compressed_opus",
            "tests/voice_samples/encoded_compressed_webm", 
            "tests/voice_samples/encoded_compressed_aac",
            "tests/voice_samples/encoded_compressed_mp3"
        ]
        
        for test_dir in test_dirs:
            if Path(test_dir).exists():
                files = list(Path(test_dir).glob("*.json"))
                if files:
                    print(f"\n{test_dir}:")
                    for file in files[:3]:  # Show first 3 files
                        print(f"  {file}")
                    if len(files) > 3:
                        print(f"  ... and {len(files) - 3} more")
        
        print(f"\nExample:")
        print(f"  python test_websocket_simple.py tests/voice_samples/encoded_compressed_opus/test_price_aapl_today_compressed_opus.json")
        return
    
    audio_file = sys.argv[1]
    
    if not Path(audio_file).exists():
        print(f"❌ File not found: {audio_file}")
        return
    
    print(f"🧪 WebSocket Audio Pipeline Test")
    print(f"=" * 50)
    
    # Run the test
    asyncio.run(test_websocket_audio(audio_file))


if __name__ == "__main__":
    main()