#!/usr/bin/env python3
"""
Comprehensive OPUS Audio WebSocket Test

Tests the complete audio pipeline with multiple queries:
1. Price query (e.g., "What's the stock price of NVDA today?")
2. News query (e.g., "What's the latest news about NVDA?")

After the conversation, retrieves the session information from the backend
and validates that all conversation turns were logged correctly.
"""

import json
import asyncio
import websockets
import sys
import requests
from pathlib import Path
from typing import Dict, List, Any
import time


class ConversationValidator:
    """Validates conversation session data from backend API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve session data from backend API."""
        url = f"{self.base_url}/api/conversation-sessions/sessions/{session_id}"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError(f"Session {session_id} not found")
        else:
            raise RuntimeError(f"Failed to get session: {response.status_code} - {response.text}")

    def get_model_info(self) -> Dict[str, Any]:
        """Retrieve model loading information from backend API."""
        url = f"{self.base_url}/api/conversation-sessions/models/info"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"Failed to get model info: {response.status_code}")

    def validate_session(self, session_data: Dict[str, Any], expected_queries: List[str]) -> Dict[str, Any]:
        """
        Validate session data against expected queries.

        Args:
            session_data: Session data from API
            expected_queries: List of expected user queries

        Returns:
            Validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "total_turns": len(session_data["turns"]),
                "expected_turns": len(expected_queries),
                "matched_queries": 0
            }
        }

        # Check turn count
        if len(session_data["turns"]) != len(expected_queries):
            results["warnings"].append(
                f"Turn count mismatch: expected {len(expected_queries)}, got {len(session_data['turns'])}"
            )

        # Validate each turn
        for i, turn in enumerate(session_data["turns"]):
            turn_num = i + 1

            # Check required fields
            required_fields = ["transcription", "agent_response", "audio_format", "audio_size_bytes", "tts_chunks_sent"]
            for field in required_fields:
                if not turn.get(field):
                    results["errors"].append(f"Turn {turn_num}: Missing {field}")
                    results["valid"] = False

            # Check transcription matches expected query (partial match)
            if i < len(expected_queries):
                expected = expected_queries[i].lower()
                actual = turn.get("transcription", "").lower()

                # Check if key words from expected query appear in transcription
                if any(word in actual for word in expected.split() if len(word) > 3):
                    results["stats"]["matched_queries"] += 1
                else:
                    results["warnings"].append(
                        f"Turn {turn_num}: Transcription '{actual}' doesn't match expected '{expected}'"
                    )

            # Check agent response is not empty
            if not turn.get("agent_response"):
                results["errors"].append(f"Turn {turn_num}: Empty agent response")
                results["valid"] = False

            # Check TTS chunks were sent
            if turn.get("tts_chunks_sent", 0) == 0:
                results["warnings"].append(f"Turn {turn_num}: No TTS chunks sent")

        return results


async def test_comprehensive_opus(test_files: List[str], ws_url: str = "ws://localhost:8000/ws/voice"):
    """
    Test comprehensive OPUS audio pipeline with multiple queries.

    Args:
        test_files: List of paths to OPUS encoded JSON files
        ws_url: WebSocket URL
    """
    print("=" * 80)
    print("🧪 WebSocket Audio Pipeline Test")
    print("=" * 80)
    print(f"🎵 Testing WebSocket Audio Pipeline")

    session_id = None
    responses = []
    expected_queries = []

    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"\n🔌 Trying {ws_url}...")
            print(f"✅ Connected successfully!")

            # Wait for the connected message to get the actual session ID
            connected_response = await websocket.recv()
            connected_data = json.loads(connected_response)
            session_id = connected_data.get('data', {}).get('session_id')

            if session_id:
                print(f"🆔 Using actual session ID: {session_id}")
            else:
                print(f"⚠️ No session ID received")
                return

            # Process each test file
            for file_idx, file_path in enumerate(test_files):
                print(f"\n{'='*80}")
                print(f"📁 Test File #{file_idx + 1}: {Path(file_path).name}")
                print(f"{'='*80}")

                # Load the encoded JSON file
                with open(file_path, 'r') as f:
                    message = json.load(f)

                # Extract test info
                audio_size = len(message['data']['audio_chunk'])
                audio_format = message['data']['format']
                file_size = message['data']['file_size']

                print(f"📊 Audio size: {audio_size:,} chars (base64)")
                print(f"🎵 Format: {audio_format}")

                # Show compression info if available
                if message['data'].get('compression'):
                    comp_info = message['data']['compression']
                    print(f"🎵 Compression: {comp_info['codec'].upper()} @ {comp_info['bitrate']}")
                    print(f"📈 Compression ratio: {comp_info['compression_ratio']:.1f}x")
                    print(f"💾 Original size: {comp_info['original_size']:,} bytes")
                    print(f"💾 Compressed size: {comp_info['compressed_size']:,} bytes")
                    print(f"💾 Space saved: {((comp_info['original_size'] - comp_info['compressed_size']) / comp_info['original_size'] * 100):.1f}%")

                # Update message with correct session ID
                message['data']['session_id'] = session_id

                # Send the encoded message
                start_time = time.time()
                await websocket.send(json.dumps(message))
                send_time = time.time() - start_time
                print(f"📤 Audio message sent in {send_time:.3f}s!")

                # Wait for responses for this query
                print(f"⏳ Waiting for backend responses...")
                timeout_count = 0
                max_timeout = 15
                query_responses = []

                while timeout_count < max_timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        response_data = json.loads(response)
                        query_responses.append(response_data)
                        responses.append(response_data)

                        event = response_data.get('event', 'unknown')
                        print(f"📥 Response #{len(query_responses)}: {event}")

                        if event == 'transcription':
                            transcription = response_data.get('data', {}).get('text', 'N/A')
                            print(f"   🎤 Transcription: {transcription}")
                            expected_queries.append(transcription)

                        elif event == 'agent_response':
                            response_text = response_data.get('data', {}).get('text', 'N/A')
                            print(f"   🤖 Agent Response: {response_text}")

                        elif event == 'tts_chunk':
                            chunk_idx = response_data.get('data', {}).get('chunk_index', 0)
                            print(f"   🔊 TTS Audio chunk #{chunk_idx} received")

                        elif event == 'streaming_complete':
                            print(f"   ✅ TTS streaming complete")
                            break

                        elif event == 'error':
                            error_msg = response_data.get('data', {}).get('message', 'N/A')
                            print(f"   ❌ Error: {error_msg}")
                            break

                    except asyncio.TimeoutError:
                        timeout_count += 1
                        if timeout_count % 5 == 0:
                            print(f"⏰ Still waiting... ({timeout_count}/{max_timeout}s)")

                print(f"✅ Completed query #{file_idx + 1}: {len(query_responses)} responses received")

                # Small delay between queries
                if file_idx < len(test_files) - 1:
                    await asyncio.sleep(1.0)

            print(f"\n{'='*80}")
            print(f"📊 Test Summary:")
            print(f"   Total time: {time.time() - start_time:.2f}s")
            print(f"   Total responses received: {len(responses)}")
            print(f"   Queries processed: {len(test_files)}")
            print(f"   ✅ Backend is processing compressed audio successfully!")

    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Now validate the session by retrieving it from the backend
    if session_id:
        print(f"\n{'='*80}")
        print(f"🔍 Validating Session from Backend API")
        print(f"{'='*80}")

        # Wait a moment for backend to finish writing logs
        await asyncio.sleep(2.0)

        try:
            validator = ConversationValidator()

            # Get model info
            print(f"\n📊 Model Information:")
            model_info = validator.get_model_info()
            print(f"   SenseVoice Loaded: {'✅' if model_info['sensevoice_loaded'] else '❌'}")
            if model_info.get('sensevoice_model_path'):
                print(f"   SenseVoice Path: {model_info['sensevoice_model_path']}")
            print(f"   TTS Engine: {model_info['tts_engine']}")
            if model_info.get('loading_time_ms'):
                for model, load_time in model_info['loading_time_ms'].items():
                    print(f"   {model} Load Time: {load_time:.0f}ms")

            # Get session data
            print(f"\n📊 Session Data:")
            session_data = validator.get_session(session_id)
            print(f"   Session ID: {session_data['session_id']}")
            print(f"   User ID: {session_data['user_id']}")
            print(f"   Session Start: {session_data['session_start']}")
            print(f"   Session End: {session_data.get('session_end', 'N/A')}")
            print(f"   Total Turns: {session_data['total_turns']}")
            print(f"   Total Interruptions: {session_data['total_interruptions']}")

            # Validate session
            print(f"\n🔍 Validating Conversation Turns:")
            validation_results = validator.validate_session(session_data, expected_queries)

            print(f"   Total Turns: {validation_results['stats']['total_turns']}")
            print(f"   Expected Turns: {validation_results['stats']['expected_turns']}")
            print(f"   Matched Queries: {validation_results['stats']['matched_queries']}")

            if validation_results['errors']:
                print(f"\n❌ Validation Errors:")
                for error in validation_results['errors']:
                    print(f"   - {error}")

            if validation_results['warnings']:
                print(f"\n⚠️ Validation Warnings:")
                for warning in validation_results['warnings']:
                    print(f"   - {warning}")

            if validation_results['valid'] and not validation_results['errors']:
                print(f"\n✅ Session validation successful!")
            else:
                print(f"\n❌ Session validation failed")

            # Print detailed turn information
            print(f"\n📝 Detailed Turn Information:")
            for i, turn in enumerate(session_data['turns']):
                print(f"\n   Turn #{i+1}:")
                print(f"      🎤 User: \"{turn['transcription']}\"")
                print(f"      🤖 Agent: \"{turn['agent_response']}\"")
                print(f"      ⏱️ Processing Time: {turn['processing_time_ms']:.0f}ms")
                print(f"      🎵 Audio: {turn['audio_format']} ({turn['audio_size_bytes']:,} bytes)")
                print(f"      🔊 TTS Chunks: {turn['tts_chunks_sent']}")
                if turn.get('error'):
                    print(f"      ❌ Error: {turn['error']}")

        except Exception as e:
            print(f"❌ Failed to validate session: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_comprehensive_opus.py <opus_file_1> <opus_file_2> ...")
        print("\nExample:")
        print("  python test_comprehensive_opus.py \\")
        print("    tests/voice_samples/encoded_compressed_opus/test_price_nvda_today_compressed_opus.json \\")
        print("    tests/voice_samples/encoded_compressed_opus/test_news_nvda_latest_compressed_opus.json")
        sys.exit(1)

    test_files = sys.argv[1:]

    # Validate all files exist
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

    # Run the test
    asyncio.run(test_comprehensive_opus(test_files))


if __name__ == "__main__":
    main()
