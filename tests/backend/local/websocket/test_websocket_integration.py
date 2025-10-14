#!/usr/bin/env python3
"""
Integrated Backend WebSocket Test using Voice Samples Config.

This test:
1. Loads voice_samples.json configuration
2. Sends encoded OPUS audio to backend WebSocket
3. Receives and validates audio responses
4. Retrieves session data via REST API
5. Validates session history against expected entities

Usage:
    # Run single sample test
    uv run python tests/test_backend_websocket_integration.py --sample-id news_nvda_latest

    # Run multi-turn scenario
    uv run python tests/test_backend_websocket_integration.py --scenario scenario_nvda_full_analysis

    # Run all tests
    uv run python -m pytest tests/test_backend_websocket_integration.py -v
"""

import asyncio
import base64
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import pytest
import requests
import websockets

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a single test."""
    sample_id: str
    success: bool
    transcription: Optional[str] = None
    expected_text: Optional[str] = None
    received_audio: bool = False
    session_id: Optional[str] = None
    error: Optional[str] = None
    processing_time_ms: float = 0
    validation_details: Dict = field(default_factory=dict)


class BackendWebSocketTester:
    """Test backend WebSocket with voice samples."""

    def __init__(self, config_path: Path, base_url: str = "http://localhost:8000"):
        """Initialize tester with configuration."""
        self.config_path = config_path
        self.base_dir = config_path.parent
        self.base_url = base_url
        self.ws_url = f"ws://localhost:8000/ws/voice/simple"  # Correct endpoint path
        self.session_api_url = f"{base_url}/api/conversation-sessions/sessions"

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.test_config = self.config.get('test_configurations', {}).get('backend_websocket_integration', {})
        self.validation_rules = self.config.get('test_configurations', {}).get('validation_rules', {})

    def get_sample_by_id(self, sample_id: str) -> Optional[Dict]:
        """Get sample data by ID."""
        for category, samples in self.config['samples'].items():
            if category == "multi_turn_scenarios":
                continue
            for sample in samples:
                if sample['id'] == sample_id:
                    return sample
        return None

    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """Get multi-turn scenario by ID."""
        scenarios = self.config['samples'].get('multi_turn_scenarios', [])
        for scenario in scenarios:
            if scenario['id'] == scenario_id:
                return scenario
        return None

    async def send_audio_sample(self, sample_id: str, user_id: str = "test-user") -> TestResult:
        """Send audio sample to backend and validate response."""
        import time

        result = TestResult(sample_id=sample_id, success=False)

        try:
            # Get sample data
            sample = self.get_sample_by_id(sample_id)
            if not sample:
                result.error = f"Sample {sample_id} not found in config"
                return result

            result.expected_text = sample['text']

            # Load encoded audio
            encoded_path = self.base_dir / sample['encoded_path']
            if not encoded_path.exists():
                result.error = f"Encoded audio not found: {encoded_path}"
                return result

            with open(encoded_path, 'r') as f:
                encoded_data = json.load(f)

            # Extract audio chunk from the event wrapper
            if 'event' in encoded_data and encoded_data['event'] == 'audio_chunk':
                audio_chunk = encoded_data['data']['audio_chunk']
            else:
                result.error = "Invalid encoded audio format"
                return result

            logger.info(f"\n{'='*60}")
            logger.info(f"Testing: {sample_id}")
            logger.info(f"Expected: {result.expected_text}")
            logger.info(f"{'='*60}")

            start_time = time.time()

            # Connect to WebSocket with proper headers for CORS
            additional_headers = {
                "Origin": "http://localhost:3000"  # Match CORS_ORIGINS setting
            }
            async with websockets.connect(self.ws_url, additional_headers=additional_headers) as websocket:
                # Wait for "connected" event (backend sends this automatically)
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                resp_data = json.loads(response)

                if resp_data.get('event') == 'connected':
                    result.session_id = resp_data['data'].get('session_id')
                    logger.info(f"Session started: {result.session_id}")
                else:
                    result.error = f"Expected 'connected' event, got {resp_data.get('event')}"
                    return result

                # Send audio chunk
                audio_message = {
                    "event": "audio_chunk",
                    "data": {
                        "audio_chunk": audio_chunk,
                        "format": "opus",
                        "is_final": True
                    }
                }
                await websocket.send(json.dumps(audio_message))
                logger.info("Sent audio chunk")

                # Collect all responses
                responses = []
                audio_chunks_received = 0
                transcription = None
                agent_response = None

                try:
                    while True:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30)  # Increased timeout for agent processing
                        resp_data = json.loads(response)
                        event = resp_data.get('event')

                        responses.append(resp_data)

                        if event == 'transcription':
                            transcription = resp_data['data'].get('text', '')
                            result.transcription = transcription
                            logger.info(f"Transcription: {transcription}")

                        elif event == 'agent_response':
                            agent_response = resp_data['data'].get('text', '')
                            logger.info(f"Agent response: {agent_response[:100]}...")

                        elif event == 'tts_chunk':
                            audio_chunks_received += 1
                            # Log first and last chunks only to avoid spam
                            if audio_chunks_received == 1:
                                logger.info(f"Receiving TTS audio chunks...")

                        elif event == 'streaming_complete':
                            logger.info(f"Received streaming_complete ({audio_chunks_received} total TTS chunks)")
                            result.received_audio = True
                            break

                        elif event == 'error':
                            result.error = resp_data['data'].get('error', 'Unknown error')
                            logger.error(f"Error from backend: {result.error}")
                            break

                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for response")
                    result.error = "Timeout waiting for streaming_complete event"

            result.processing_time_ms = (time.time() - start_time) * 1000

            # Validate results
            if result.transcription and result.received_audio:
                result.success = True
                logger.info(f"✓ Test passed in {result.processing_time_ms:.0f}ms")
            else:
                result.error = result.error or "Missing transcription or audio response"
                logger.error(f"✗ Test failed: {result.error}")

        except Exception as e:
            result.error = f"Exception: {str(e)}"
            logger.error(f"Test error: {e}", exc_info=True)

        return result

    async def validate_session(self, session_id: str, expected_entities: List[str]) -> Dict:
        """Validate session data against expected entities."""
        validation = {
            "session_found": False,
            "entities_found": [],
            "entities_missing": [],
            "conversation_turns": 0
        }

        try:
            # Retrieve session from API
            url = f"{self.session_api_url}/{session_id}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                validation["session_found"] = True
                session_data = response.json()

                # Count conversation turns
                turns = session_data.get('conversation_turns', [])
                validation["conversation_turns"] = len(turns)

                # Check for expected entities in conversation history
                conversation_text = json.dumps(session_data).lower()

                for entity in expected_entities:
                    if entity.lower() in conversation_text:
                        validation["entities_found"].append(entity)
                    else:
                        validation["entities_missing"].append(entity)

                logger.info(f"Session validation: {len(validation['entities_found'])}/{len(expected_entities)} entities found")

            else:
                logger.warning(f"Failed to retrieve session: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"Session validation error: {e}")

        return validation

    async def run_scenario(self, scenario_id: str) -> List[TestResult]:
        """Run multi-turn scenario."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found")
            return []

        logger.info(f"\n{'#'*60}")
        logger.info(f"# Running Scenario: {scenario_id}")
        logger.info(f"# {scenario.get('description', '')}")
        logger.info(f"{'#'*60}\n")

        results = []
        user_id = f"test-user-{scenario_id}"

        for turn_id in scenario['turns']:
            result = await self.send_audio_sample(turn_id, user_id=user_id)
            results.append(result)

            if not result.success:
                logger.error(f"Scenario failed at turn: {turn_id}")
                break

            # Small delay between turns
            await asyncio.sleep(1)

        # Validate final session if we have a session_id
        if results and results[-1].session_id:
            expected_entities = scenario.get('expected_session_entities', [])
            validation = await self.validate_session(results[-1].session_id, expected_entities)
            results[-1].validation_details = validation

        return results

    def print_summary(self, results: List[TestResult]):
        """Print test summary."""
        passed = sum(1 for r in results if r.success)
        total = len(results)

        logger.info(f"\n{'='*60}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")

        if total - passed > 0:
            logger.info(f"\nFailed Tests:")
            for r in results:
                if not r.success:
                    logger.info(f"  - {r.sample_id}: {r.error}")

        logger.info(f"{'='*60}\n")


# Pytest fixtures and tests
@pytest.fixture
def tester():
    """Create tester instance."""
    config_path = Path(__file__).parent / 'voice_samples' / 'voice_samples.json'
    return BackendWebSocketTester(config_path)


@pytest.mark.asyncio
async def test_nvda_news_query(tester):
    """Test NVDA news query with session validation."""
    result = await tester.send_audio_sample('news_nvda_latest')

    assert result.success, f"Test failed: {result.error}"
    assert result.transcription is not None, "No transcription received"
    assert result.received_audio, "No audio response received"

    # Validate session contains NVDA/NVIDIA (optional - may not be implemented in all backends)
    if result.session_id:
        validation = await tester.validate_session(result.session_id, ['NVDA', 'NVIDIA'])
        # Only assert if session API is available
        if validation['session_found']:
            assert len(validation['entities_found']) > 0, "Expected entities not found in session"
        else:
            logger.warning("Session API not available or session not persisted - skipping validation")


@pytest.mark.asyncio
async def test_price_query(tester):
    """Test stock price query."""
    result = await tester.send_audio_sample('price_aapl')

    assert result.success, f"Test failed: {result.error}"
    assert result.transcription is not None, "No transcription received"
    assert result.received_audio, "No audio response received"


@pytest.mark.asyncio
async def test_watchlist_add(tester):
    """Test adding stock to watchlist."""
    result = await tester.send_audio_sample('watchlist_add_nvda')

    assert result.success, f"Test failed: {result.error}"
    assert result.transcription is not None, "No transcription received"
    assert result.received_audio, "No audio response received"


@pytest.mark.asyncio
async def test_full_nvda_scenario(tester):
    """Test complete NVDA news analysis scenario."""
    results = await tester.run_scenario('scenario_nvda_full_analysis')

    assert len(results) > 0, "No results from scenario"
    assert all(r.success for r in results), "Some turns failed in scenario"

    # Check final session validation (optional - may not be implemented in all backends)
    final_result = results[-1]
    if final_result.validation_details and final_result.validation_details.get('session_found'):
        assert len(final_result.validation_details['entities_found']) > 0, "Expected entities not found"
    else:
        logger.warning("Session API not available or session not persisted - skipping validation")


# CLI interface
async def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test backend WebSocket integration")
    parser.add_argument('--sample-id', type=str, help='Test specific sample ID')
    parser.add_argument('--scenario', type=str, help='Run multi-turn scenario')
    parser.add_argument('--config', type=Path,
                        default=Path(__file__).parent / 'voice_samples' / 'voice_samples.json',
                        help='Path to voice_samples.json')

    args = parser.parse_args()

    tester = BackendWebSocketTester(args.config)

    if args.sample_id:
        result = await tester.send_audio_sample(args.sample_id)
        tester.print_summary([result])
        sys.exit(0 if result.success else 1)

    elif args.scenario:
        results = await tester.run_scenario(args.scenario)
        tester.print_summary(results)
        sys.exit(0 if all(r.success for r in results) else 1)

    else:
        print("Please specify --sample-id or --scenario")
        print("\nExamples:")
        print("  uv run python tests/test_backend_websocket_integration.py --sample-id news_nvda_latest")
        print("  uv run python tests/test_backend_websocket_integration.py --scenario scenario_nvda_full_analysis")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
