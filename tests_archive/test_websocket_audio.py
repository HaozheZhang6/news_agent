#!/usr/bin/env python3
"""Test sending audio files via WebSocket to Voice News Agent backend."""

import asyncio
import json
import websockets
import base64
import sys
import os
from pathlib import Path

async def send_audio_file(websocket, audio_file_path: str, session_id: str, user_id: str):
    """Send an audio file in chunks via WebSocket."""
    try:
        print(f"📁 Reading audio file: {audio_file_path}")
        
        # Read the audio file
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        print(f"📊 Audio file size: {len(audio_data)} bytes")
        
        # Determine format from file extension
        file_ext = Path(audio_file_path).suffix.lower()
        if file_ext in ['.wav', '.wave']:
            format_type = "wav"
        elif file_ext in ['.mp3']:
            format_type = "mp3"
        elif file_ext in ['.webm']:
            format_type = "webm"
        elif file_ext in ['.ogg']:
            format_type = "ogg"
        else:
            format_type = "wav"  # default
            print(f"⚠️ Unknown format {file_ext}, using 'wav'")
        
        print(f"🎵 Audio format: {format_type}")
        
        # Method 1: Send as single chunk (simpler)
        print("📤 Sending audio as single chunk...")
        audio_b64 = base64.b64encode(audio_data).decode()
        
        message = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": audio_b64,
                "format": format_type,
                "is_final": True,
                "session_id": session_id,
                "user_id": user_id
            }
        }
        
        await websocket.send(json.dumps(message))
        print("✅ Audio sent!")
        
        # Wait for response
        print("⏳ Waiting for response...")
        response = await websocket.recv()
        print(f"📥 Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending audio file: {e}")
        return False

async def send_audio_chunks(websocket, audio_file_path: str, session_id: str, user_id: str, chunk_size: int = 4096):
    """Send an audio file in multiple chunks (for streaming simulation)."""
    try:
        print(f"📁 Reading audio file for chunked sending: {audio_file_path}")
        
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        file_ext = Path(audio_file_path).suffix.lower()
        format_type = "wav" if file_ext in ['.wav', '.wave'] else "mp3"
        
        print(f"📊 Audio file size: {len(audio_data)} bytes")
        print(f"📦 Chunk size: {chunk_size} bytes")
        print(f"🎵 Audio format: {format_type}")
        
        # Send audio in chunks
        total_chunks = (len(audio_data) + chunk_size - 1) // chunk_size
        print(f"📤 Sending {total_chunks} chunks...")
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            is_final = (i + chunk_size) >= len(audio_data)
            
            audio_b64 = base64.b64encode(chunk).decode()
            
            message = {
                "event": "voice_data",
                "data": {
                    "audio_chunk": audio_b64,
                    "format": format_type,
                    "is_final": is_final,
                    "session_id": session_id,
                    "user_id": user_id
                }
            }
            
            await websocket.send(json.dumps(message))
            print(f"📤 Sent chunk {i//chunk_size + 1}/{total_chunks} ({len(chunk)} bytes, final: {is_final})")
            
            # Small delay between chunks
            await asyncio.sleep(0.1)
            
            # Check for responses
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                print(f"📥 Response: {response}")
            except asyncio.TimeoutError:
                pass  # No response yet, continue
        
        print("✅ All chunks sent!")
        
        # Wait for final response
        print("⏳ Waiting for final response...")
        final_response = await websocket.recv()
        print(f"📥 Final response: {final_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending audio chunks: {e}")
        return False

async def test_websocket_audio(url: str, audio_file_path: str = None):
    """Test WebSocket connection and send audio."""
    try:
        print(f"🔌 Connecting to {url}...")
        async with websockets.connect(url) as websocket:
            print("✅ Connected successfully!")
            
            # Generate test session
            import uuid
            session_id = str(uuid.uuid4())
            user_id = "03f6b167-0c4d-4983-a380-54b8eb42f830"
            
            print(f"🆔 Session ID: {session_id}")
            print(f"👤 User ID: {user_id}")
            
            if audio_file_path and os.path.exists(audio_file_path):
                print(f"\n🎵 Testing with audio file: {audio_file_path}")
                
                # Test both methods
                print("\n=== Method 1: Single chunk ===")
                await send_audio_file(websocket, audio_file_path, session_id, user_id)
                
                print("\n=== Method 2: Multiple chunks ===")
                await send_audio_chunks(websocket, audio_file_path, session_id, user_id)
                
            else:
                print("\n📝 Testing with text command (no audio file)...")
                
                # Send text command as fallback
                test_message = {
                    "event": "voice_command",
                    "data": {
                        "command": "tell me the news",
                        "user_id": user_id,
                        "session_id": session_id
                    }
                }
                
                print(f"📤 Sending: {json.dumps(test_message, indent=2)}")
                await websocket.send(json.dumps(test_message))
                
                response = await websocket.recv()
                print(f"📥 Received: {response}")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def create_test_audio():
    """Create a simple test audio file (WAV format)."""
    try:
        import wave
        import numpy as np
        
        # Create a simple sine wave
        sample_rate = 16000
        duration = 2  # seconds
        frequency = 440  # Hz (A note)
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        
        # Save as WAV
        with wave.open('test_audio.wav', 'w') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        print("✅ Created test_audio.wav")
        return 'test_audio.wav'
        
    except ImportError:
        print("⚠️ numpy/wave not available, cannot create test audio")
        return None
    except Exception as e:
        print(f"❌ Error creating test audio: {e}")
        return None

if __name__ == "__main__":
    # Default to local backend
    url = "ws://localhost:8000/ws/voice"
    audio_file = None
    
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "render":
            url = "wss://voice-news-agent-api.onrender.com/ws/voice"
        elif sys.argv[1].startswith("ws"):
            url = sys.argv[1]
        else:
            audio_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        audio_file = sys.argv[2]
    
    # If no audio file provided, try to create a test one
    if not audio_file:
        print("📝 No audio file provided, creating test audio...")
        audio_file = create_test_audio()
    
    print(f"🎯 Testing WebSocket at: {url}")
    if audio_file:
        print(f"🎵 Audio file: {audio_file}")
    
    asyncio.run(test_websocket_audio(url, audio_file))
