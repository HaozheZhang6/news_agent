# Test Suite Index

Complete index of all tests in the News Agent project.

## Quick Navigation

- [Backend Tests](#backend-tests)
  - [WebSocket Tests](#websocket-tests)
  - [API Tests](#api-tests)
  - [Core Tests](#core-tests)
- [Frontend Tests](#frontend-tests)
  - [Component Tests](#component-tests)
  - [Utils Tests](#utils-tests)
- [Integration Tests](#integration-tests)
- [Test Utilities](#test-utilities)
- [Archived Tests](#archived-tests)

---

## Backend Tests

### WebSocket Tests

**Location:** `tests/backend/local/websocket/`

| Test File | Purpose | Requirements | Key Tests |
|-----------|---------|--------------|-----------|
| `test_websocket_integration.py` | Voice sample-based WebSocket integration | Backend server, voice samples | Single sample test, multi-turn scenarios, session validation |
| `test_websocket_wav_audio.py` | Comprehensive WAV audio pipeline testing | Backend server | Connection test, WAV encoding, audio streaming, error handling |

#### test_websocket_wav_audio.py Details

```bash
# Run all WAV audio tests
uv run python -m pytest tests/backend/local/websocket/test_websocket_wav_audio.py -v

# Run specific test
uv run python -m pytest tests/backend/local/websocket/test_websocket_wav_audio.py::test_websocket_connection -v
```

**Test Coverage:**
- ✓ Basic WebSocket connection
- ✓ Init message and session creation
- ✓ Send simple WAV audio (sine wave)
- ✓ Send speech-like audio (multiple frequencies)
- ✓ WAV header validation
- ✓ Multiple audio chunks in one session
- ✓ Empty/silent audio handling
- ✓ Invalid WAV format error handling
- ✓ Different sample rates (8kHz, 16kHz, 24kHz, 48kHz)

#### test_websocket_integration.py Details

```bash
# Run with specific voice sample
uv run python tests/backend/local/websocket/test_websocket_integration.py --sample-id news_nvda_latest

# Run multi-turn scenario
uv run python tests/backend/local/websocket/test_websocket_integration.py --scenario scenario_nvda_full_analysis
```

**Test Coverage:**
- ✓ Voice sample loading from JSON config
- ✓ OPUS audio decoding and sending
- ✓ Transcription validation
- ✓ TTS audio response validation
- ✓ Session history via REST API
- ✓ Entity extraction validation

---

### API Tests

**Location:** `tests/backend/local/api/`

| Test File | Purpose | Requirements | Endpoints Tested |
|-----------|---------|--------------|------------------|
| `test_api_news.py` | News endpoint functionality | Backend server, Supabase | `/api/news/*` |
| `test_api_user.py` | User management | Backend server, Supabase | `/api/users/*` |
| `test_api_voice.py` | Voice API endpoints | Backend server | `/api/voice/*` |
| `test_api_conversation_log.py` | Conversation logging | Backend server, Supabase | `/api/conversation-sessions/*` |
| `test_api_profile.py` | User profile management | Backend server, Supabase | `/api/profile/*` |

#### Running API Tests

```bash
# All API tests
uv run python -m pytest tests/backend/local/api/ -v

# Specific API test file
uv run python -m pytest tests/backend/local/api/test_api_news.py -v

# Specific test function
uv run python -m pytest tests/backend/local/api/test_api_news.py::test_get_latest_news -v
```

---

### Core Tests

**Location:** `tests/backend/local/core/`

| Test File | Purpose | Requirements | Components Tested |
|-----------|---------|--------------|-------------------|
| `test_sensevoice_integration.py` | SenseVoice ASR functionality | Backend server, SenseVoice model | Audio transcription, language detection |
| `test_voice.py` | Voice processing utilities | Backend server | Audio encoding/decoding, format conversion |
| `test_core_agent_wrapper.py` | Agent wrapper logic | Backend server | Agent initialization, message handling |
| `test_core_websocket_manager.py` | WebSocket manager | Backend server | Session management, connection handling |

#### Running Core Tests

```bash
# All core tests
uv run python -m pytest tests/backend/local/core/ -v

# SenseVoice tests only
uv run python -m pytest tests/backend/local/core/test_sensevoice_integration.py -v
```

---

## Frontend Tests

### Component Tests

**Location:** `tests/frontend/local/components/`

| Test File | Purpose | Requirements | Key Features Tested |
|-----------|---------|--------------|---------------------|
| `test_continuous_voice_interface.html` | ContinuousVoiceInterface component | Backend server, browser | WebSocket, session, audio send/receive, VAD |

#### test_continuous_voice_interface.html

**How to Run:**
```bash
# Option 1: Open directly in browser
open tests/frontend/local/components/test_continuous_voice_interface.html

# Option 2: Serve via HTTP server
cd tests/frontend/local/components
python -m http.server 8080
# Then open: http://localhost:8080/test_continuous_voice_interface.html
```

**Test Coverage:**
- ✓ Test 1: WebSocket Connection
- ✓ Test 2: Session Creation
- ✓ Test 3: Send WAV Audio
- ✓ Test 4: Receive TTS Audio
- ✓ Test 5: VAD Simulation
- ✓ Test 6: Reconnection

**Features:**
- Interactive test controls
- Real-time metrics (total tests, passed, failed, avg latency)
- Console log viewer
- Visual pass/fail indicators

---

### Utils Tests

**Location:** `tests/frontend/local/utils/`

| Test File | Purpose | Requirements | Functions Tested |
|-----------|---------|--------------|------------------|
| `test_wav_encoder.html` | WAV encoder utility | Browser | WAV encoding, PCM conversion, header validation |

#### test_wav_encoder.html

**How to Run:**
```bash
open tests/frontend/local/utils/test_wav_encoder.html
```

**Test Coverage:**
- ✓ WAV header format (RIFF, WAVE, fmt, data chunks)
- ✓ Sample rate encoding (8kHz, 16kHz, 24kHz, 48kHz)
- ✓ Float32 to 16-bit PCM conversion
- ✓ File size calculation
- ✓ Sine wave encoding
- ✓ Sample clipping (values outside [-1, 1])
- ✓ Empty audio handling
- ✓ Different duration encoding
- ✓ Mono/stereo channel encoding

**Auto-runs on load:** All tests execute automatically when page opens

---

## Integration Tests

**Location:** `tests/integration/`

| Test File | Purpose | Requirements | Scope |
|-----------|---------|--------------|-------|
| `test_api_integration.py` | Full API integration | Backend server, Supabase | End-to-end API flows |

```bash
# Run integration tests
uv run python -m pytest tests/integration/ -v
```

---

## Test Utilities

### Voice Sample Configuration

**Location:** `tests/voice_samples/voice_samples.json`

Configuration for voice test samples including:
- Sample text and audio paths
- Expected entities and intents
- Multi-turn scenarios
- Test configurations

### Audio Generation

**Location:** `tests/utils/generate_test_audio.py`

```bash
# Generate all missing audio samples
uv run python tests/utils/generate_test_audio.py

# Generate specific category
uv run python tests/utils/generate_test_audio.py --sample-id news

# Regenerate all (overwrite)
uv run python tests/utils/generate_test_audio.py --regenerate-all
```

### Voice Encoder

**Location:** `tests/testing_utils/voice_encoder.py`

Utility for encoding audio samples to various formats (OPUS, WAV, etc.)

---

## Archived Tests

**Location:** `tests/archive/`

### Old Root Tests

**Location:** `tests/archive/old_root_tests/`

Archived test files from project root before reorganization:
- `test_audio_websocket.sh`
- `test_audio_ws.html`
- `test_frontend_ws.html`
- `test_ws_connection.py`
- `test_ws_simple.html`

### Legacy Tests

**Location:** `tests/archive/`

- `test_agent.py` - Original agent logic tests
- `test_interruption_scenarios.py` - Old interruption handling tests
- `test_parallel_communication.py` - Old parallel communication tests
- `test_preference_learning.py` - Old preference learning tests
- `test_voice_interaction.py` - Old voice interaction tests

**Why Archived:**
These tests were written for older implementations and are kept for reference. Current tests cover the same functionality with updated APIs.

---

## Test Execution Summary

### Run All Backend Tests

```bash
# All backend local tests
uv run python -m pytest tests/backend/local/ -v

# With coverage
uv run python -m pytest tests/backend/local/ -v --cov=backend --cov-report=html
```

### Run All Frontend Tests

```bash
# Open component tests
open tests/frontend/local/components/test_continuous_voice_interface.html

# Open utils tests
open tests/frontend/local/utils/test_wav_encoder.html
```

### Run Integration Tests

```bash
# Voice sample integration
uv run python tests/backend/local/websocket/test_websocket_integration.py --sample-id news_nvda_latest

# Full integration suite
uv run python -m pytest tests/integration/ -v
```

---

## Test Requirements by Category

### Backend Local Tests
- ✓ Backend server running (`make run-server`)
- ✓ Supabase credentials configured
- ✓ SenseVoice model loaded
- ✓ TTS service available

### Frontend Local Tests
- ✓ Backend server running
- ✓ Modern browser (Chrome, Firefox, Safari)
- ✓ Microphone access (for some tests)

### Integration Tests
- ✓ Backend server running
- ✓ Voice samples generated
- ✓ Supabase database accessible

---

## Test Metrics

### Backend Test Count
- WebSocket tests: 2 files, ~20 test functions
- API tests: 5 files, ~30 test functions
- Core tests: 4 files, ~25 test functions
- **Total Backend: ~75 tests**

### Frontend Test Count
- Component tests: 1 file, 6 tests
- Utils tests: 1 file, 9 tests
- **Total Frontend: ~15 tests**

### Integration Test Count
- API integration: 1 file, ~10 tests
- **Total Integration: ~10 tests**

### **Grand Total: ~100 comprehensive tests**

---

## Quick Reference Commands

```bash
# Backend WebSocket tests
uv run python -m pytest tests/backend/local/websocket/ -v

# Backend API tests
uv run python -m pytest tests/backend/local/api/ -v

# Backend core tests
uv run python -m pytest tests/backend/local/core/ -v

# All backend tests
uv run python -m pytest tests/backend/local/ -v

# Frontend component tests (browser)
open tests/frontend/local/components/test_continuous_voice_interface.html

# Frontend utils tests (browser)
open tests/frontend/local/utils/test_wav_encoder.html

# Integration tests
uv run python -m pytest tests/integration/ -v

# Specific voice sample test
uv run python tests/backend/local/websocket/test_websocket_integration.py --sample-id news_nvda_latest

# Generate audio samples
uv run python tests/utils/generate_test_audio.py
```

---

## Related Documentation

- [README.md](./README.md) - Main test documentation
- [TEST_STRUCTURE.md](./TEST_STRUCTURE.md) - Test organization guide
- [voice_samples.json](./voice_samples/voice_samples.json) - Voice test configuration
- [AUDIO_TESTING_GUIDE.md](./testing_utils/AUDIO_TESTING_GUIDE.md) - Audio testing guide

---

## Support

For test issues or questions:
1. Check backend logs: `logs/conversations/`
2. Review test output with `-v` flag
3. Verify backend server is running
4. Check Supabase connection
5. Ensure audio samples are generated
