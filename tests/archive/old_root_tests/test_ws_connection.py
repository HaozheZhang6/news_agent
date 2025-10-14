#!/usr/bin/env python3
"""
Test WebSocket connection to verify the fix for immediate disconnection bug.
"""
import asyncio
import json
import websockets
import sys

async def test_websocket_connection():
    """Test WebSocket connection and verify it stays open."""
    uri = "ws://localhost:8000/ws/voice?user_id=test_user_001"

    print(f"🔌 Connecting to {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")

            # Wait for the 'connected' message from backend
            print("⏳ Waiting for 'connected' message from backend...")

            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 Received message: {json.dumps(data, indent=2)}")

                if data.get("event") == "connected" or data.get("type") == "connected":
                    session_id = data.get("data", {}).get("session_id")
                    print(f"✅ Connection successful! Session ID: {session_id}")

                    # Keep connection alive for a moment to verify it stays open
                    print("⏳ Keeping connection alive for 2 seconds...")
                    await asyncio.sleep(2)

                    print("✅ Connection remained stable for 2 seconds!")

                    # Send a test voice command message
                    test_message = {
                        "event": "voice_command",
                        "data": {
                            "command": "What's the latest news?",
                            "session_id": session_id,
                            "confidence": 0.95
                        }
                    }
                    print(f"📤 Sending test message: {json.dumps(test_message, indent=2)}")
                    await websocket.send(json.dumps(test_message))

                    # Wait for multiple responses (transcription, voice_response, TTS chunks)
                    print("⏳ Waiting for responses (max 20 seconds)...")
                    responses_received = 0
                    for i in range(10):  # Expect multiple messages
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                            data = json.loads(response)
                            responses_received += 1
                            print(f"📨 Response {responses_received}: event={data.get('event')}")
                            if data.get("event") == "voice_response":
                                print(f"   Text: {data.get('data', {}).get('text', 'N/A')[:100]}...")
                        except asyncio.TimeoutError:
                            print(f"⏱️ No more messages after waiting for response {i+1}")
                            break

                    if responses_received > 0:
                        print(f"✅ WebSocket test PASSED! Received {responses_received} responses")
                        return True
                    else:
                        print("❌ No responses received from backend")
                        return False
                else:
                    print(f"❌ Unexpected message event/type: {data.get('event') or data.get('type')}")
                    return False

            except asyncio.TimeoutError:
                print("❌ Timeout waiting for 'connected' message")
                return False

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket closed unexpectedly: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    print("=" * 60)
    print("WebSocket Connection Test")
    print("=" * 60)

    success = await test_websocket_connection()

    print("=" * 60)
    if success:
        print("✅ TEST PASSED")
        sys.exit(0)
    else:
        print("❌ TEST FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
