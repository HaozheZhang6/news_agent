# News Agent Test Suite

Comprehensive testing infrastructure for the News Agent backend.

## Overview

This test suite provides:
1. **Voice Sample Configuration**: JSON-based test case definitions
2. **Audio Generation**: Automated TTS + OPUS encoding pipeline
3. **Integration Tests**: Full WebSocket + REST API validation
4. **Multi-Turn Scenarios**: Complex conversation flow testing

## Quick Start

### 1. Start Backend Server

```bash
# Terminal 1: Start backend
make run-server
```

### 2. Run Integration Tests

```bash
# Single sample test
uv run python tests/test_backend_websocket_integration.py --sample-id news_nvda_latest

# Multi-turn scenario
uv run python tests/test_backend_websocket_integration.py --scenario scenario_nvda_full_analysis

# Run all pytest tests
uv run python -m pytest tests/test_backend_websocket_integration.py -v
```

## Voice Samples Configuration

### Location
- `tests/voice_samples/voice_samples.json` - Master configuration file
- `tests/voice_samples/wav/` - Generated WAV audio files
- `tests/voice_samples/encoded_compressed_opus/` - OPUS encoded JSON files

### Configuration Structure

```json
{
  "samples": {
    "stock_price_queries": [...],
    "news_queries": [...],
    "watchlist_operations": [...],
    "deep_dive_analysis": [...],
    "follow_up_queries": [...],
    "multi_turn_scenarios": [...]
  },
  "test_configurations": {
    "backend_websocket_integration": {...},
    "validation_rules": {...}
  }
}
```

### Sample Format

```json
{
  "id": "news_nvda_latest",
  "text": "What's the latest news about NVIDIA?",
  "wav_path": "wav/test_news_nvda_latest.wav",
  "encoded_path": "encoded_compressed_opus/test_news_nvda_latest_compressed_opus.json",
  "expected_entities": ["NVDA", "NVIDIA", "news", "latest"],
  "expected_intent": "news_query"
}
```

### Multi-Turn Scenarios

```json
{
  "id": "scenario_nvda_full_analysis",
  "description": "Complete NVDA news analysis with follow-ups",
  "turns": [
    "news_nvda_latest",
    "analysis_nvda_deeper",
    "followup_caused_movement"
  ],
  "expected_session_entities": ["NVDA", "NVIDIA", "news", "analysis", "price", "movement"]
}
```

## Generating Audio Samples

### Generate All Missing Samples

```bash
uv run python tests/utils/generate_test_audio.py
```

### Generate Specific Category

```bash
# Stock price queries
uv run python tests/utils/generate_test_audio.py --sample-id price

# Watchlist operations
uv run python tests/utils/generate_test_audio.py --sample-id watchlist

# News queries
uv run python tests/utils/generate_test_audio.py --sample-id news
```

### Regenerate All (Overwrite Existing)

```bash
uv run python tests/utils/generate_test_audio.py --regenerate-all
```

### Requirements

The generation script requires:
- **TTS Engine**: `edge-tts` (preferred) or `gtts`
- **Audio Processing**: `ffmpeg` with Opus support

Install dependencies:
```bash
uv pip install edge-tts  # or gtts
brew install ffmpeg      # macOS
```

## Integration Test Features

### Single Sample Testing

Test individual voice samples:

```bash
uv run python tests/test_backend_websocket_integration.py --sample-id <sample_id>
```

**What it does:**
1. Loads encoded OPUS audio from config
2. Connects to WebSocket (`ws://localhost:8000/api/ws/voice`)
3. Sends init message and receives session_id
4. Sends audio chunk
5. Validates transcription received
6. Validates audio response received
7. Retrieves session data from REST API
8. Validates expected entities in session history

### Multi-Turn Scenario Testing

Test complete conversation flows:

```bash
uv run python tests/test_backend_websocket_integration.py --scenario <scenario_id>
```

**Example Scenarios:**

- `scenario_nvda_full_analysis` - News + deep dive + follow-up
- `scenario_aapl_price_and_watchlist` - Price check + add to watchlist
- `scenario_tsla_news_deep_dive` - News + detailed analysis

### Pytest Integration

Run tests via pytest for CI/CD integration:

```bash
# Run all integration tests
uv run python -m pytest tests/test_backend_websocket_integration.py -v

# Run specific test
uv run python -m pytest tests/test_backend_websocket_integration.py::test_nvda_news_query -v

# Run with coverage
uv run python -m pytest tests/test_backend_websocket_integration.py --cov=backend --cov-report=html
```

## Test Categories

### Essential Tests (Keep)

These tests are actively maintained and used:

1. **`test_backend_websocket_integration.py`** - Main integration test suite
2. **`test_agent.py`** - Agent logic tests
3. **`test_voice.py`** - Voice processing tests
4. **`test_api_*.py`** - API endpoint tests
5. **`test_sensevoice_integration.py`** - SenseVoice ASR tests

### Archived Tests

Older tests moved to `tests_archive/` for reference:

- `test_audio_pipeline.py`
- `test_voice_pipeline.py`
- `test_compressed_audio.py`
- `test_websocket_simple.py`
- etc.

## Validation Rules

Tests validate:

### Response Validation
- **Transcription received**: Audio correctly transcribed
- **Audio response received**: TTS audio sent back
- **Processing time**: Response within timeout
- **Session ID**: Valid session created

### Content Validation
- **Expected entities**: Key terms found in responses
- **Intent matching**: Request understood correctly
- **Context preservation**: Multi-turn context maintained

### Session Validation (via REST API)
- **Session retrieval**: GET `/api/conversation-sessions/sessions/{session_id}`
- **Conversation history**: All turns logged
- **Entity presence**: Expected entities in session data

## Example Test Output

```
============================================================
Testing: news_nvda_latest
Expected: What's the latest news about NVIDIA?
============================================================
Session started: 03f6b167-0c4d-4983-a380-54b8eb42f830
Sent audio chunk
Transcription: What's the latest news about NVIDIA?
Received final audio chunk (15 total)
✓ Test passed in 3245ms
Session validation: 2/2 entities found

============================================================
TEST SUMMARY
============================================================
Total: 1
Passed: 1
Failed: 0
Success Rate: 100.0%
============================================================
```

## Adding New Test Cases

### 1. Add Sample to Configuration

Edit `tests/voice_samples/voice_samples.json`:

```json
{
  "id": "news_meta_latest",
  "text": "What's the latest news about Meta?",
  "wav_path": "wav/test_news_meta_latest.wav",
  "encoded_path": "encoded_compressed_opus/test_news_meta_latest_compressed_opus.json",
  "expected_entities": ["META", "Meta", "news", "latest"],
  "expected_intent": "news_query"
}
```

### 2. Generate Audio

```bash
uv run python tests/utils/generate_test_audio.py --sample-id news_meta_latest
```

### 3. Run Test

```bash
uv run python tests/test_backend_websocket_integration.py --sample-id news_meta_latest
```

### 4. Add to Scenarios (Optional)

```json
{
  "id": "scenario_meta_analysis",
  "description": "Meta news and analysis",
  "turns": ["news_meta_latest", "analysis_meta_deeper"],
  "expected_session_entities": ["META", "Meta", "news", "analysis"]
}
```

## Troubleshooting

### WebSocket 403 Error

**Error**: `server rejected WebSocket connection: HTTP 403`

**Root Cause**: CORS origin mismatch or wrong endpoint path

**Solution**: Already fixed in the code! The test now:
- Uses correct endpoint: `ws://localhost:8000/ws/voice/simple`
- Includes Origin header: `http://localhost:3000`

If you still see this error, verify:
1. Backend is running on port 8000
2. CORS settings in `backend/app/config.py` include the test origin

### Backend Not Running

**Error**: `Connection refused (Errno 61)`

**Solution**:
```bash
# Start backend server
make run-server

# Or manually
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Expected startup output:
```
✅ WebSocketManager initialized successfully
✅ SenseVoice model loaded successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Audio Generation Fails

**Error**: `ffmpeg not found` or `No TTS engine available`

**Solution**:
```bash
# Install ffmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Linux

# Install TTS engine
uv pip install edge-tts  # Recommended
```

### Transcription Mismatch

If transcription doesn't match expected text:

1. Check audio quality: `ffplay tests/voice_samples/wav/test_*.wav`
2. Verify SenseVoice model loaded: Check backend logs
3. Adjust expected_entities instead of exact text match

### Timeout Errors

Increase timeout in test configuration:

```json
{
  "test_configurations": {
    "backend_websocket_integration": {
      "timeout_seconds": 60
    }
  }
}
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
- name: Run Integration Tests
  run: |
    make run-server &
    sleep 5
    uv run python -m pytest tests/test_backend_websocket_integration.py -v
    kill %1
```

## Related Documentation

- [AUDIO_TESTING_GUIDE.md](./testing_utils/AUDIO_TESTING_GUIDE.md) - Detailed audio pipeline docs
- [voice_samples.json](./voice_samples/voice_samples.json) - Master test configuration
- [generate_test_audio.py](./utils/generate_test_audio.py) - Audio generation script

## Support

For issues or questions:
1. Check backend logs: `logs/conversations/`
2. Review test output with `-v` flag
3. Verify audio samples exist and are valid
4. Check backend server is running on port 8000
