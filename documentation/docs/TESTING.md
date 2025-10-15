# Testing Guide

Comprehensive guide for testing the Voice News Agent application, covering backend services, WebSocket connections, audio processing, and integration testing.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [WebSocket Testing](#websocket-testing)
- [Audio Testing](#audio-testing)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [Test Fixtures](#test-fixtures)
- [Common Test Patterns](#common-test-patterns)
- [Troubleshooting](#troubleshooting)
- [Coverage Guidelines](#coverage-guidelines)
- [Best Practices](#best-practices)

---

## Overview

The testing suite is organized into several categories:

- **Backend Tests**: API endpoints, WebSocket handlers, core services
- **Source Tests**: Voice input/output, agent logic
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Load testing, benchmarks

All tests use `pytest` as the testing framework with async support via `pytest-asyncio`.

---

## Test Structure

```
tests/
├── conftest.py                          # Global fixtures and configuration
├── run_tests.py                         # Test runner script
├── backend/
│   ├── local/
│   │   ├── api/                        # API endpoint tests
│   │   │   ├── test_api_user.py
│   │   │   ├── test_api_voice.py
│   │   │   ├── test_api_news.py
│   │   │   └── test_api_conversation_log.py
│   │   ├── core/                       # Core service tests
│   │   │   ├── test_core_websocket_manager.py
│   │   │   ├── test_core_agent_wrapper.py
│   │   │   └── test_voice.py
│   │   └── websocket/                  # WebSocket integration tests
│   │       ├── test_websocket_integration.py
│   │       └── test_websocket_wav_audio.py
│   ├── cloud/                          # Cloud deployment tests
│   └── mutual/                         # Shared backend tests
├── src/                                # Source component tests
│   ├── test_agent.py
│   ├── test_voice_input.py
│   └── test_voice_output.py
├── integration/                        # End-to-end tests
│   └── test_api_integration.py
├── testing_utils/                      # Test utilities
│   └── voice_encoder.py
└── voice_samples/                      # Test audio samples
    ├── voice_samples.json              # Sample configuration
    └── encoded/                        # Pre-encoded audio files
```

---

## Setup

### 1. Install Test Dependencies

```bash
# Install test dependencies with uv
make install-test

# Or manually with uv
uv sync --extra test
```

### 2. Environment Configuration

Tests use a separate test environment configuration defined in `tests/conftest.py`:

```python
os.environ.update({
    'ENVIRONMENT': 'test',
    'DEBUG': 'true',
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_KEY': 'test-key',
    # ... other test environment variables
})
```

For integration tests that require real services, create a `.env.test` file:

```bash
cp env_files/env.example .env.test
# Edit .env.test with test credentials
```

### 3. Start Test Server (for integration tests)

```bash
# Start backend server on port 8000
make run-server

# Or with HuggingFace Space ASR only
make run-server-hf
```

---

## Running Tests

### All Tests

```bash
# Run all tests using the test runner
make run-tests

# Or directly with pytest
uv run pytest tests/ -v
```

### Specific Test Categories

```bash
# Backend tests only
make test-backend
# Equivalent: uv run pytest tests/backend/ -v --tb=short --timeout=15

# Source component tests only
make test-src
# Equivalent: uv run pytest tests/src/ -v --tb=short --timeout=15

# Integration tests only
make test-integration
# Equivalent: uv run pytest tests/integration/ -v --tb=short --timeout=15

# Fast tests (exclude slow tests)
make test-fast
# Equivalent: uv run pytest tests/ -v -m "not slow" --timeout=15
```

### Specific Test Files

```bash
# Run specific test file
uv run pytest tests/backend/local/websocket/test_websocket_integration.py -v

# Run specific test class
uv run pytest tests/backend/local/core/test_core_websocket_manager.py::TestWebSocketManager -v

# Run specific test function
uv run pytest tests/backend/local/api/test_api_voice.py::TestVoiceAPI::test_voice_command_endpoint -v
```

### Coverage Reports

```bash
# Generate coverage report
make test-coverage
# Equivalent: uv run pytest tests/ --cov=backend --cov=src --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html
```

### Parallel Testing

```bash
# Run tests in parallel using pytest-xdist
uv run pytest tests/ -n auto
```

---

## WebSocket Testing

### Connection Tests

Test basic WebSocket connection establishment and lifecycle:

```python
@pytest.mark.asyncio
async def test_websocket_connection(ws_url):
    """Test basic WebSocket connection."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:
        assert websocket.open
        print("✓ WebSocket connection established")
```

**File**: `tests/backend/local/websocket/test_websocket_wav_audio.py:172-183`

### Session Initialization

Test WebSocket session initialization and session ID assignment:

```python
@pytest.mark.asyncio
async def test_websocket_init_message(ws_url):
    """Test sending init message and receiving session_id."""
    async with websockets.connect(
        ws_url,
        extra_headers={"Origin": "http://localhost:3000"}
    ) as websocket:
        # Send init message
        init_msg = {
            "event": "init",
            "user_id": "test-user-001"
        }
        await websocket.send(json.dumps(init_msg))

        # Wait for session_started message
        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(response)

        assert data.get("event") == "session_started"
        assert "session_id" in data
        assert len(data["session_id"]) > 0
```

**File**: `tests/backend/local/websocket/test_websocket_wav_audio.py:186-210`

### Message Format Tests

Test WebSocket message formats for different event types:

```python
# Event format validation
message_formats = {
    "connected": {
        "event": "connected",
        "data": {
            "session_id": str,
            "timestamp": str
        }
    },
    "transcription": {
        "event": "transcription",
        "data": {
            "text": str,
            "confidence": float
        }
    },
    "tts_chunk": {
        "event": "tts_chunk",
        "data": {
            "audio_chunk": str,  # base64 encoded
            "format": str
        }
    },
    "streaming_complete": {
        "event": "streaming_complete",
        "data": {}
    }
}
```

### Error Handling Tests

Test WebSocket error scenarios:

```python
@pytest.mark.asyncio
async def test_invalid_wav_format(ws_url):
    """Test sending invalid WAV data."""
    async with websockets.connect(ws_url) as websocket:
        # Initialize session
        init_msg = {"event": "init", "user_id": "test-user-001"}
        await websocket.send(json.dumps(init_msg))

        response = await websocket.recv()
        session_data = json.loads(response)
        session_id = session_data["session_id"]

        # Send invalid WAV data
        invalid_data = b"NOT A WAV FILE"
        invalid_base64 = base64.b64encode(invalid_data).decode('utf-8')

        audio_msg = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": invalid_base64,
                "format": "wav",
                "is_final": True,
                "session_id": session_id
            }
        }

        await websocket.send(json.dumps(audio_msg))

        # Should receive error or handle gracefully
        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        data = json.loads(response)
        # Backend should handle gracefully
```

**File**: `tests/backend/local/websocket/test_websocket_wav_audio.py:495-537`

### Performance Tests

Test WebSocket performance and timing:

```python
@pytest.mark.asyncio
async def test_send_audio_sample(self, sample_id: str, user_id: str = "test-user") -> TestResult:
    """Send audio sample and measure performance."""
    import time

    start_time = time.time()

    # ... WebSocket operations ...

    result.processing_time_ms = (time.time() - start_time) * 1000

    if result.success:
        logger.info(f"✓ Test passed in {result.processing_time_ms:.0f}ms")
```

**File**: `tests/backend/local/websocket/test_websocket_integration.py:97-220`

---

## Audio Testing

### WAV Audio Generation

Generate test audio for WebSocket testing:

```python
class WAVEncoder:
    """Simple WAV encoder for test audio generation."""

    def __init__(self, sample_rate: int = 16000, num_channels: int = 1, bit_depth: int = 16):
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.bit_depth = bit_depth

    def encode_from_pcm(self, pcm_samples: List[float]) -> bytes:
        """Encode PCM samples to WAV format."""
        # Convert float32 samples to int16
        int16_samples = [int(max(-32768, min(32767, s * 32767))) for s in pcm_samples]

        # Pack samples as 16-bit little-endian integers
        pcm_data = struct.pack('<' + 'h' * len(int16_samples), *int16_samples)

        # Build WAV header and chunks
        # ... (see full implementation in file)

        return header + fmt_chunk + data_chunk + pcm_data
```

**File**: `tests/backend/local/websocket/test_websocket_wav_audio.py:46-96`

### Test Audio Generators

Generate different types of test audio:

```python
def generate_sine_wave(frequency: float, duration: float, sample_rate: int = 16000) -> List[float]:
    """Generate a sine wave for testing."""
    import math
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = math.sin(2.0 * math.pi * frequency * t)
        samples.append(sample)
    return samples

def generate_test_speech(duration: float = 2.0, sample_rate: int = 16000) -> List[float]:
    """Generate test "speech-like" audio using multiple sine waves."""
    frequencies = [200, 400, 800, 1600]  # Hz (speech formants)
    amplitudes = [0.3, 0.2, 0.15, 0.1]

    # Mix frequencies with envelope
    # ... (see full implementation in file)
```

**File**: `tests/backend/local/websocket/test_websocket_wav_audio.py:98-157`

### Audio Transcription Tests

Test audio transcription pipeline:

```python
@pytest.mark.asyncio
async def test_send_wav_audio_simple(ws_url, wav_encoder):
    """Test sending simple WAV audio and receiving transcription."""
    async with websockets.connect(ws_url) as websocket:
        # Initialize session
        init_msg = {"event": "init", "user_id": "test-user-001"}
        await websocket.send(json.dumps(init_msg))

        # Generate and send test audio
        pcm_samples = generate_sine_wave(440, 2.0, 16000)
        wav_data = wav_encoder.encode_from_pcm(pcm_samples)
        wav_base64 = base64.b64encode(wav_data).decode('utf-8')

        audio_msg = {
            "event": "audio_chunk",
            "data": {
                "audio_chunk": wav_base64,
                "format": "wav",
                "is_final": True,
                "session_id": session_id,
                "user_id": "test-user-001",
                "sample_rate": 16000,
                "file_size": len(wav_data)
            }
        }

        await websocket.send(json.dumps(audio_msg))

        # Collect responses
        received_transcription = False
        received_audio = False

        for _ in range(20):
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(response)
            event = data.get("event")

            if event == "transcription":
                received_transcription = True
            elif event == "audio_chunk":
                received_audio = True
            elif event == "audio_end":
                break

        assert received_audio or received_transcription
```

**File**: `tests/backend/local/websocket/test_websocket_wav_audio.py:213-282`

### Voice Sample Configuration

Use pre-recorded voice samples for realistic testing:

```json
{
  "samples": {
    "news_queries": [
      {
        "id": "news_nvda_latest",
        "text": "What's the latest news about NVIDIA?",
        "audio_path": "voice_samples/nvda_news.wav",
        "encoded_path": "voice_samples/encoded/nvda_news.json",
        "expected_entities": ["NVDA", "NVIDIA"]
      }
    ]
  }
}
```

**Usage**:

```python
config_path = Path(__file__).parent / 'voice_samples' / 'voice_samples.json'
tester = BackendWebSocketTester(config_path)
result = await tester.send_audio_sample('news_nvda_latest')
```

**File**: `tests/backend/local/websocket/test_websocket_integration.py:64-77`

### Sample Rate Testing

Test different audio sample rates:

```python
@pytest.mark.asyncio
async def test_different_sample_rates(ws_url, wav_encoder):
    """Test WAV files with different sample rates."""
    sample_rates = [8000, 16000, 24000, 48000]

    for sr in sample_rates:
        encoder = WAVEncoder(sample_rate=sr)

        # Generate audio at this sample rate
        pcm_samples = generate_sine_wave(440, 1.0, sr)
        wav_data = encoder.encode_from_pcm(pcm_samples)

        # Send and verify
        # ...
```

**File**: `tests/backend/local/websocket/test_websocket_wav_audio.py:541-589`

---

## Unit Testing

### Mocking Dependencies

Use pytest fixtures for mocking external dependencies:

```python
@pytest.fixture
def mock_database() -> AsyncMock:
    """Mock database for testing."""
    mock_db = AsyncMock()
    mock_db.health_check.return_value = True
    mock_db.get_user.return_value = {
        "id": "test-user",
        "email": "test@example.com",
        "subscription_tier": "free"
    }
    return mock_db

@pytest.fixture
def mock_agent() -> AsyncMock:
    """Mock agent for testing."""
    mock_agent = AsyncMock()
    mock_agent.process_text_command.return_value = {
        "response_text": "Test response",
        "response_type": "agent_response",
        "processing_time_ms": 100
    }
    return mock_agent
```

**File**: `tests/conftest.py:40-142`

### WebSocket Manager Tests

Test WebSocket manager core functionality:

```python
class TestWebSocketManager:
    """Test WebSocket manager functionality."""

    @pytest.fixture
    async def ws_manager(self, mock_database, mock_cache, mock_agent):
        """Create WebSocket manager instance for testing."""
        manager = WebSocketManager()
        manager.db = mock_database
        manager.cache = mock_cache
        manager.agent = mock_agent
        manager._initialized = True
        return manager

    async def test_connect(self, ws_manager, mock_websocket):
        """Test WebSocket connection."""
        user_id = "test-user"

        with patch.object(ws_manager.db, 'create_conversation_session') as mock_create_session:
            mock_create_session.return_value = {"id": "session-123"}

            session_id = await ws_manager.connect(mock_websocket, user_id)

        assert session_id is not None
        assert session_id in ws_manager.active_connections
        mock_websocket.accept.assert_called_once()

    async def test_send_message(self, ws_manager, mock_websocket):
        """Test sending message to WebSocket."""
        session_id = "test-session"
        ws_manager.active_connections[session_id] = mock_websocket

        message = {"event": "test", "data": {"message": "test"}}
        await ws_manager.send_message(session_id, message)

        mock_websocket.send_text.assert_called_once()
```

**File**: `tests/backend/local/core/test_core_websocket_manager.py:8-89`

### API Endpoint Tests

Test REST API endpoints:

```python
class TestVoiceAPI:
    """Test voice API endpoints."""

    def test_voice_command_endpoint(self, test_client):
        """Test voice command processing endpoint."""
        with patch('backend.app.api.voice.get_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.process_voice_command.return_value = {
                "response_text": "Here are today's headlines...",
                "response_type": "agent_response",
                "processing_time_ms": 150,
                "session_id": "test-session"
            }
            mock_get_agent.return_value = mock_agent

            response = test_client.post(
                "/api/voice/command",
                json={
                    "command": "tell me the news",
                    "user_id": "test-user",
                    "session_id": "test-session",
                    "confidence": 0.95
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["response_text"] == "Here are today's headlines..."

    def test_voice_health_check(self, test_client):
        """Test voice health check endpoint."""
        response = test_client.get("/api/voice/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
```

**File**: `tests/backend/local/api/test_api_voice.py:10-94`

---

## Integration Testing

### End-to-End WebSocket Test

Test complete WebSocket workflow with voice samples:

```python
@pytest.mark.asyncio
async def test_nvda_news_query(tester):
    """Test NVDA news query with session validation."""
    # Send audio sample through WebSocket
    result = await tester.send_audio_sample('news_nvda_latest')

    # Verify transcription received
    assert result.success, f"Test failed: {result.error}"
    assert result.transcription is not None, "No transcription received"
    assert result.received_audio, "No audio response received"

    # Validate session contains expected entities
    if result.session_id:
        validation = await tester.validate_session(
            result.session_id,
            ['NVDA', 'NVIDIA']
        )
        if validation['session_found']:
            assert len(validation['entities_found']) > 0
```

**File**: `tests/backend/local/websocket/test_websocket_integration.py:327-344`

### Multi-Turn Scenarios

Test conversation flows with multiple turns:

```python
@pytest.mark.asyncio
async def test_full_nvda_scenario(tester):
    """Test complete NVDA news analysis scenario."""
    # Run multi-turn scenario
    results = await tester.run_scenario('scenario_nvda_full_analysis')

    assert len(results) > 0, "No results from scenario"
    assert all(r.success for r in results), "Some turns failed in scenario"

    # Check final session validation
    final_result = results[-1]
    if final_result.validation_details:
        assert len(final_result.validation_details['entities_found']) > 0
```

**File**: `tests/backend/local/websocket/test_websocket_integration.py:367-380`

---

## Test Fixtures

### Global Fixtures

Defined in `tests/conftest.py`:

```python
# Event loop
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for test session."""

# Mock services
@pytest.fixture
def mock_database() -> AsyncMock:
    """Mock database for testing."""

@pytest.fixture
def mock_cache() -> AsyncMock:
    """Mock cache for testing."""

@pytest.fixture
def mock_agent() -> AsyncMock:
    """Mock agent for testing."""

@pytest.fixture
def mock_websocket() -> Mock:
    """Mock WebSocket for testing."""

# Test clients
@pytest.fixture
def test_client():
    """Test client for FastAPI testing."""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    return TestClient(app)

@pytest.fixture
async def async_test_client():
    """Async test client for FastAPI testing."""
    from httpx import AsyncClient
    from backend.app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Sample data
@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""

@pytest.fixture
def sample_news_data() -> dict:
    """Sample news data for testing."""

@pytest.fixture
def sample_stock_data() -> dict:
    """Sample stock data for testing."""
```

### Local Fixtures

Test-specific fixtures:

```python
@pytest.fixture
def ws_url():
    """WebSocket URL for testing."""
    return "ws://localhost:8000/ws/voice/simple"

@pytest.fixture
def wav_encoder():
    """WAV encoder instance."""
    return WAVEncoder(sample_rate=16000, num_channels=1, bit_depth=16)

@pytest.fixture
def tester():
    """Create tester instance."""
    config_path = Path(__file__).parent / 'voice_samples' / 'voice_samples.json'
    return BackendWebSocketTester(config_path)
```

---

## Common Test Patterns

### Async Test Pattern

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Mocking with Patch

```python
def test_with_mock():
    """Test with mocked dependency."""
    with patch('module.path.function') as mock_func:
        mock_func.return_value = "mocked result"

        result = function_under_test()

        assert result == "expected result"
        mock_func.assert_called_once()
```

### Timeout Pattern

```python
@pytest.mark.asyncio
async def test_with_timeout():
    """Test with timeout."""
    try:
        response = await asyncio.wait_for(
            websocket.recv(),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        pytest.fail("Operation timed out")
```

### Parametrized Tests

```python
@pytest.mark.parametrize("sample_rate,expected", [
    (8000, True),
    (16000, True),
    (24000, True),
    (48000, True),
])
async def test_sample_rates(sample_rate, expected):
    """Test different sample rates."""
    result = await process_audio(sample_rate)
    assert result == expected
```

### Error Testing

```python
def test_error_handling():
    """Test error handling."""
    with pytest.raises(ValueError) as exc_info:
        function_that_raises_error()

    assert "expected error message" in str(exc_info.value)
```

---

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Refused

**Symptom**: `ConnectionRefusedError: [Errno 61] Connection refused`

**Solution**:
```bash
# Ensure backend server is running
make run-server

# Check if port 8000 is available
lsof -ti :8000
```

#### 2. Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'backend'`

**Solution**:
```bash
# Ensure Python path includes project root
export PYTHONPATH=/Users/haozhezhang/Documents/Agents/News_agent:$PYTHONPATH

# Or use uv run which handles this automatically
uv run pytest tests/
```

#### 3. Timeout Errors

**Symptom**: `asyncio.TimeoutError` during WebSocket tests

**Solution**:
```python
# Increase timeout in test
response = await asyncio.wait_for(websocket.recv(), timeout=30.0)  # Increased from 5.0

# Or in pytest.ini
[tool.pytest.ini_options]
addopts = ["--timeout=30"]
```

#### 4. Missing Test Dependencies

**Symptom**: `ModuleNotFoundError: No module named 'pytest_asyncio'`

**Solution**:
```bash
# Install test dependencies
make install-test
# Or: uv sync --extra test
```

#### 5. Mock Database Errors

**Symptom**: Tests fail with database connection errors

**Solution**:
```python
# Ensure mock_database fixture is used
def test_function(mock_database):
    # Test uses mock instead of real database
    pass

# Check conftest.py sets test environment
os.environ['ENVIRONMENT'] = 'test'
```

#### 6. WAV Audio Format Errors

**Symptom**: `ValueError: Invalid WAV file format`

**Solution**:
```python
# Verify WAV header
wav_data = wav_encoder.encode_from_pcm(samples)
assert wav_data[0:4] == b'RIFF'
assert wav_data[8:12] == b'WAVE'

# Check sample rate matches
assert audio_msg["data"]["sample_rate"] == 16000
```

### Debug Tips

#### Enable Verbose Logging

```bash
# Run tests with verbose output
uv run pytest tests/ -v -s

# Show stdout/stderr
uv run pytest tests/ -v -s --capture=no

# Show detailed traceback
uv run pytest tests/ -v --tb=long
```

#### Run Single Test with Debug

```bash
# Run specific test with prints
uv run pytest tests/backend/local/websocket/test_websocket_integration.py::test_nvda_news_query -v -s

# Add breakpoint in test
import pdb; pdb.set_trace()
```

#### Check Test Environment

```python
# Add to test to check environment
def test_environment_check():
    import os
    print(f"ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    print(f"CWD: {os.getcwd()}")
```

---

## Coverage Guidelines

### Target Coverage

- **Overall**: 80% minimum
- **Core Services**: 90% minimum (WebSocketManager, Agent, Database)
- **API Endpoints**: 85% minimum
- **Utilities**: 70% minimum

### Generate Coverage Report

```bash
# Generate HTML coverage report
make test-coverage

# View report
open htmlcov/index.html

# Terminal coverage summary
uv run pytest tests/ --cov=backend --cov=src --cov-report=term
```

### Coverage Configuration

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["backend", "src"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### Check Uncovered Code

```bash
# Show missing lines
uv run pytest tests/ --cov=backend --cov-report=term-missing

# Generate detailed report
uv run pytest tests/ --cov=backend --cov-report=html
# View htmlcov/index.html to see uncovered lines highlighted
```

---

## Best Practices

### 1. Test Organization

- **One test class per module**: `TestWebSocketManager` for `websocket_manager.py`
- **Descriptive test names**: `test_websocket_connection_with_invalid_headers`
- **Group related tests**: Use test classes to group related functionality
- **Use markers**: `@pytest.mark.slow`, `@pytest.mark.integration`

### 2. Test Independence

```python
# GOOD: Each test is independent
def test_create_user(mock_database):
    user = create_user("test@example.com")
    assert user is not None

def test_get_user(mock_database):
    user = get_user("test-id")
    assert user is not None

# BAD: Tests depend on each other
def test_create_and_get_user(mock_database):
    user = create_user("test@example.com")
    retrieved = get_user(user.id)  # Depends on previous operation
```

### 3. Mock External Services

```python
# Always mock external dependencies
@pytest.fixture
def mock_database():
    """Mock database to avoid external dependency."""
    return AsyncMock()

# Mock API calls
with patch('module.requests.get') as mock_get:
    mock_get.return_value.json.return_value = {"data": "test"}
```

### 4. Use Fixtures for Setup

```python
# GOOD: Use fixtures for common setup
@pytest.fixture
def initialized_manager(mock_database, mock_cache):
    manager = WebSocketManager()
    manager.db = mock_database
    manager.cache = mock_cache
    manager._initialized = True
    return manager

def test_manager_connect(initialized_manager):
    # Manager is already set up
    pass

# BAD: Repeat setup in every test
def test_manager_connect():
    manager = WebSocketManager()
    manager.db = mock_database  # Repeated setup
    manager.cache = mock_cache
    # ...
```

### 5. Test Error Conditions

```python
# Test both success and failure paths
async def test_websocket_send_success(ws_manager):
    """Test successful message send."""
    await ws_manager.send_message("session-id", {"event": "test"})
    # Assert success

async def test_websocket_send_disconnected(ws_manager):
    """Test send to disconnected client."""
    await ws_manager.send_message("invalid-session", {"event": "test"})
    # Should not raise exception
```

### 6. Async Testing

```python
# Always use @pytest.mark.asyncio for async tests
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# Use asyncio.wait_for for timeouts
response = await asyncio.wait_for(
    websocket.recv(),
    timeout=5.0
)
```

### 7. Clear Assertions

```python
# GOOD: Clear, specific assertions
assert response.status_code == 200
assert data["event"] == "transcription"
assert len(results) > 0

# BAD: Vague or multiple assertions
assert response  # What are we checking?
assert data  # Too vague
```

### 8. Cleanup Resources

```python
# Use context managers for cleanup
async with websockets.connect(url) as websocket:
    # Test code
    pass  # WebSocket auto-closes

# Or use fixtures with cleanup
@pytest.fixture
async def connected_websocket():
    websocket = await websockets.connect(url)
    yield websocket
    await websocket.close()
```

### 9. Test Data Management

```python
# Use fixtures for test data
@pytest.fixture
def sample_voice_command():
    return {
        "command": "tell me the news",
        "user_id": "test-user",
        "confidence": 0.95
    }

# Use voice_samples.json for audio test data
config_path = Path(__file__).parent / 'voice_samples' / 'voice_samples.json'
```

### 10. Documentation

```python
# Always include docstrings
def test_websocket_connection():
    """
    Test basic WebSocket connection establishment.

    Verifies:
    - Connection can be established to ws://localhost:8000
    - WebSocket remains open after connection
    - CORS headers are properly handled
    """
    pass
```

### 11. Performance Considerations

```python
# Measure performance for critical paths
import time

start_time = time.time()
result = await process_audio(audio_data)
processing_time = (time.time() - start_time) * 1000

assert processing_time < 1000, f"Processing too slow: {processing_time}ms"
```

### 12. Use Test Markers

```python
# Mark slow tests
@pytest.mark.slow
def test_large_dataset():
    pass

# Mark integration tests
@pytest.mark.integration
async def test_end_to_end():
    pass

# Run only fast tests
# uv run pytest -m "not slow"
```

---

## Running Tests with Make

The project includes convenient Make targets for common testing scenarios:

```bash
# Run all tests
make run-tests

# Run specific test suites
make test-backend
make test-src
make test-integration

# Run with coverage
make test-coverage

# Run only fast tests
make test-fast

# Clean test artifacts
make clean
```

See `Makefile` for all available test commands and options.

---

## Additional Resources

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **WebSockets Library**: https://websockets.readthedocs.io/
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/

---

## Contributing Tests

When adding new features:

1. **Write tests first** (TDD approach)
2. **Ensure tests pass** before submitting PR
3. **Maintain or improve coverage** - aim for 80%+ overall
4. **Document test patterns** if introducing new testing approaches
5. **Update this guide** if adding new test categories or patterns

For questions or issues with testing, see the project's GitHub issues or contact the development team.
