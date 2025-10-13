#!/usr/bin/env python3
"""
Render WebSocket Deployment Test Script

This script tests the WebSocket connection on your deployed Render server
using the same voice samples as the local integration tests.

Usage:
    # Test with specific sample
    python scripts/test_render_websocket.py --sample-id news_nvda_latest --url https://your-app.onrender.com

    # Test with default sample and URL
    python scripts/test_render_websocket.py

    # Test multiple samples
    python scripts/test_render_websocket.py --sample-id price_aapl,news_nvda_latest --url https://your-app.onrender.com
"""

import argparse
import asyncio
import base64
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

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
    """Result of a WebSocket test."""
    sample_id: str
    success: bool
    error: Optional[str] = None
    response_time: Optional[float] = None
    audio_chunks_received: int = 0
    session_id: Optional[str] = None
    transcript: Optional[str] = None


class RenderWebSocketTester:
    """Test WebSocket connection on deployed Render server."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.ws_url = f"{self.base_url.replace('http', 'ws')}/ws/voice/simple"
        self.timeout = timeout
        self.voice_samples_path = project_root / "tests" / "voice_samples" / "voice_samples.json"
        
    def load_voice_samples(self) -> Dict:
        """Load voice samples configuration."""
        try:
            with open(self.voice_samples_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Voice samples file not found: {self.voice_samples_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in voice samples: {e}")
            sys.exit(1)
    
    def find_sample(self, sample_id: str, samples_config: Dict) -> Optional[Dict]:
        """Find a sample by ID in the configuration."""
        for category, samples in samples_config.get('samples', {}).items():
            if isinstance(samples, list):
                for sample in samples:
                    if sample.get('id') == sample_id:
                        return sample
        return None
    
    def load_encoded_audio(self, encoded_path: str) -> bytes:
        """Load encoded audio data from file."""
        full_path = project_root / "tests" / "voice_samples" / encoded_path
        try:
            with open(full_path, 'r') as f:
                data = json.load(f)
                # Handle nested structure: data.data.audio_chunk
                if 'data' in data and 'audio_chunk' in data['data']:
                    return base64.b64decode(data['data']['audio_chunk'])
                # Fallback to old structure: data.audio_data
                elif 'audio_data' in data:
                    return base64.b64decode(data['audio_data'])
                else:
                    logger.error(f"Invalid encoded audio file structure: {list(data.keys())}")
                    return None
        except FileNotFoundError:
            logger.error(f"Encoded audio file not found: {full_path}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid encoded audio file: {e}")
            return None
    
    async def test_websocket_connection(self, sample_id: str) -> TestResult:
        """Test WebSocket connection with a specific sample."""
        logger.info(f"Testing WebSocket connection for sample: {sample_id}")
        
        # Load voice samples
        samples_config = self.load_voice_samples()
        sample = self.find_sample(sample_id, samples_config)
        
        if not sample:
            return TestResult(
                sample_id=sample_id,
                success=False,
                error=f"Sample '{sample_id}' not found in configuration"
            )
        
        # Load encoded audio
        audio_data = self.load_encoded_audio(sample['encoded_path'])
        if not audio_data:
            return TestResult(
                sample_id=sample_id,
                success=False,
                error=f"Failed to load audio data for sample '{sample_id}'"
            )
        
        start_time = time.time()
        audio_chunks_received = 0
        session_id = None
        transcript = None
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                logger.info(f"Connected to WebSocket: {self.ws_url}")
                
                # Send audio data
                logger.info(f"Sending audio data ({len(audio_data)} bytes)...")
                await websocket.send(audio_data)
                
                # Receive responses
                logger.info("Waiting for responses...")
                while True:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        
                        if isinstance(response, bytes):
                            # Audio response
                            audio_chunks_received += 1
                            logger.info(f"Received audio chunk #{audio_chunks_received} ({len(response)} bytes)")
                        else:
                            # Text response (JSON)
                            try:
                                data = json.loads(response)
                                logger.info(f"Received JSON response: {data}")
                                
                                if 'session_id' in data:
                                    session_id = data['session_id']
                                if 'transcript' in data:
                                    transcript = data['transcript']
                                if 'status' in data and data['status'] == 'complete':
                                    logger.info("Received completion signal")
                                    break
                            except json.JSONDecodeError:
                                logger.warning(f"Received non-JSON text response: {response}")
                        
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for response, checking if connection is still alive...")
                        try:
                            await websocket.ping()
                        except websockets.exceptions.ConnectionClosed:
                            logger.info("Connection closed by server")
                            break
                        continue
                        
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed: {e}")
            return TestResult(
                sample_id=sample_id,
                success=False,
                error=f"Connection closed: {e}",
                response_time=time.time() - start_time,
                audio_chunks_received=audio_chunks_received,
                session_id=session_id,
                transcript=transcript
            )
        except Exception as e:
            logger.error(f"WebSocket test failed: {e}")
            return TestResult(
                sample_id=sample_id,
                success=False,
                error=str(e),
                response_time=time.time() - start_time,
                audio_chunks_received=audio_chunks_received,
                session_id=session_id,
                transcript=transcript
            )
        
        response_time = time.time() - start_time
        
        # Determine success based on received responses
        success = audio_chunks_received > 0 or transcript is not None
        
        return TestResult(
            sample_id=sample_id,
            success=success,
            response_time=response_time,
            audio_chunks_received=audio_chunks_received,
            session_id=session_id,
            transcript=transcript
        )
    
    def test_health_endpoint(self, max_retries: int = 3) -> bool:
        """Test if the health endpoint is accessible."""
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=10)
                if response.status_code == 200:
                    logger.info(f"Health check passed: {response.json()}")
                    return True
                elif response.status_code == 503:
                    if attempt < max_retries - 1:
                        logger.warning(f"Health check returned 503 (Service Unavailable) - attempt {attempt + 1}/{max_retries}")
                        logger.info("Waiting for deployment to wake up...")
                        time.sleep(5)
                        continue
                    else:
                        logger.warning(f"Health check returned 503 after {max_retries} attempts")
                        logger.info("This is normal for Render free tier deployments that spin down after inactivity")
                        logger.info("Proceeding with WebSocket test anyway...")
                        return True
                else:
                    logger.error(f"Health check failed: {response.status_code}")
                    return False
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info("Waiting and retrying...")
                    time.sleep(5)
                    continue
                else:
                    logger.error(f"Connection failed after {max_retries} attempts: {e}")
                    logger.info("This might mean the deployment is not running or the URL is incorrect")
                    return False
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return False
        
        return False
    
    def print_results(self, results: List[TestResult]):
        """Print test results in a formatted way."""
        print("\n" + "="*80)
        print("RENDER WEBSOCKET TEST RESULTS")
        print("="*80)
        
        for result in results:
            print(f"\nSample: {result.sample_id}")
            print(f"Status: {'✅ PASS' if result.success else '❌ FAIL'}")
            
            if result.error:
                print(f"Error: {result.error}")
            
            if result.response_time:
                print(f"Response Time: {result.response_time:.2f}s")
            
            if result.audio_chunks_received > 0:
                print(f"Audio Chunks Received: {result.audio_chunks_received}")
            
            if result.session_id:
                print(f"Session ID: {result.session_id}")
            
            if result.transcript:
                print(f"Transcript: {result.transcript}")
        
        # Summary
        passed = sum(1 for r in results if r.success)
        total = len(results)
        print(f"\nSummary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your Render deployment is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test WebSocket connection on Render deployment")
    parser.add_argument(
        "--sample-id",
        default="news_nvda_latest",
        help="Sample ID to test (comma-separated for multiple)"
    )
    parser.add_argument(
        "--url",
        default="https://voice-news-agent-api.onrender.com",
        help="Base URL of your Render deployment"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="WebSocket timeout in seconds"
    )
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="Only test health endpoint, skip WebSocket tests"
    )
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = RenderWebSocketTester(args.url, args.timeout)
    
    print(f"Testing Render deployment at: {args.url}")
    print(f"WebSocket URL: {tester.ws_url}")
    
    # Test health endpoint first
    print("\n1. Testing health endpoint...")
    if not tester.test_health_endpoint():
        print("❌ Health check failed. Deployment may not be ready.")
        sys.exit(1)
    
    if args.health_only:
        print("✅ Health check passed. Exiting as requested.")
        return
    
    # Test WebSocket connections
    print("\n2. Testing WebSocket connections...")
    sample_ids = [s.strip() for s in args.sample_id.split(',')]
    results = []
    
    for sample_id in sample_ids:
        result = await tester.test_websocket_connection(sample_id)
        results.append(result)
    
    # Print results
    tester.print_results(results)
    
    # Exit with appropriate code
    if all(r.success for r in results):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
