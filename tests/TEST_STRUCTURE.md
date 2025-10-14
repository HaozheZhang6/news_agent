# Test Organization Structure

This document describes the organized test structure for the News Agent project.

## Directory Structure

```
tests/
├── backend/                    # Backend tests
│   ├── local/                 # Local development tests (requires local server)
│   │   ├── websocket/         # WebSocket integration tests
│   │   ├── api/               # REST API endpoint tests
│   │   └── core/              # Core business logic tests
│   ├── cloud/                 # Cloud-specific tests (Supabase, Render, etc.)
│   └── mutual/                # Tests that work in both local and cloud
│
├── frontend/                   # Frontend tests
│   ├── local/                 # Local development tests (requires dev server)
│   │   ├── components/        # React component tests
│   │   └── utils/             # Utility function tests
│   ├── cloud/                 # Cloud deployment tests (E2E)
│   └── mutual/                # Tests that work in both local and cloud
│
├── integration/                # Full system integration tests
├── testing_utils/             # Shared testing utilities
├── utils/                     # Test data generation utilities
└── voice_samples/             # Voice test data and configurations

```

## Test Categories

### Backend Tests

#### Local Tests (`tests/backend/local/`)
Tests that require a locally running backend server.

**WebSocket Tests** (`websocket/`):
- Real-time voice communication
- Audio streaming (upload/download)
- Session management
- Connection handling and reconnection
- Error scenarios

**API Tests** (`api/`):
- REST endpoint functionality
- Request/response validation
- Authentication/authorization
- Rate limiting
- Error handling

**Core Tests** (`core/`):
- Business logic units
- Service layer tests
- Data processing
- Model inference (SenseVoice, TTS)

#### Cloud Tests (`tests/backend/cloud/`)
Tests for cloud-specific functionality:
- Supabase integration (database, auth, storage)
- Render deployment validation
- Redis caching (Upstash)
- Environment-specific configurations

#### Mutual Tests (`tests/backend/mutual/`)
Tests that work in both local and cloud environments:
- Database operations (using connection string)
- Authentication flows
- Data models and schemas

### Frontend Tests

#### Local Tests (`tests/frontend/local/`)
Tests that require a locally running frontend dev server.

**Component Tests** (`components/`):
- React component rendering
- User interactions
- State management
- Props validation
- Audio player component
- Voice interface component

**Utils Tests** (`utils/`):
- Audio encoding/decoding
- WAV encoder
- WebSocket utilities
- Helper functions

#### Cloud Tests (`tests/frontend/cloud/`)
Tests for deployed frontend:
- End-to-end user flows
- Production environment validation
- Performance testing
- Browser compatibility

#### Mutual Tests (`tests/frontend/mutual/`)
Tests that work in both local and cloud:
- Pure utility functions
- Data transformations
- Validation logic

## Running Tests

### Backend Tests

```bash
# All backend local tests
uv run python -m pytest tests/backend/local/ -v

# WebSocket tests only
uv run python -m pytest tests/backend/local/websocket/ -v

# API tests only
uv run python -m pytest tests/backend/local/api/ -v

# Core logic tests
uv run python -m pytest tests/backend/local/core/ -v

# Cloud tests (requires cloud credentials)
uv run python -m pytest tests/backend/cloud/ -v

# Mutual tests (works anywhere)
uv run python -m pytest tests/backend/mutual/ -v
```

### Frontend Tests

```bash
# Component tests
cd frontend
npm test -- src/__tests__/components/

# Utils tests
npm test -- src/__tests__/utils/

# E2E tests
npm run test:e2e
```

### Integration Tests

```bash
# Full system integration
uv run python -m pytest tests/integration/ -v
```

## Test Naming Conventions

### Backend Tests
- `test_<feature>_<scenario>.py` - General test file
- `test_websocket_<functionality>.py` - WebSocket tests
- `test_api_<endpoint>.py` - API endpoint tests
- `test_<service>_integration.py` - Integration tests

### Frontend Tests
- `<Component>.test.tsx` - Component tests
- `<utility>.test.ts` - Utility tests
- `<feature>.e2e.test.ts` - E2E tests

## Test Requirements

### Local Backend Tests
1. Backend server running: `make run-server`
2. Supabase credentials in `env_files/supabase.env`
3. Required models loaded (SenseVoice, TTS)

### Local Frontend Tests
1. Frontend dev server: `cd frontend && npm run dev`
2. Backend server running (for integration tests)
3. Test environment configured

### Cloud Tests
1. Valid cloud credentials
2. Deployed services accessible
3. Test user accounts configured

## Test Data

### Voice Samples
- Configuration: `tests/voice_samples/voice_samples.json`
- WAV files: `tests/voice_samples/wav/`
- Encoded audio: `tests/voice_samples/encoded_compressed_opus/`

### Test Utilities
- Audio generation: `tests/utils/generate_test_audio.py`
- Voice encoder: `tests/testing_utils/voice_encoder.py`
- Shared fixtures: `tests/conftest.py`

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-local:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start backend
        run: make run-server &
      - name: Wait for backend
        run: sleep 10
      - name: Run backend local tests
        run: uv run python -m pytest tests/backend/local/ -v

  backend-cloud:
    runs-on: ubuntu-latest
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
    steps:
      - uses: actions/checkout@v3
      - name: Run cloud tests
        run: uv run python -m pytest tests/backend/cloud/ -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install deps
        run: cd frontend && npm install
      - name: Run tests
        run: cd frontend && npm test
```

## Migration Guide

### Moving Existing Tests

1. **Identify test type**: local, cloud, or mutual
2. **Determine category**: websocket, api, core, component, utils
3. **Move to appropriate directory**
4. **Update imports** to reflect new path
5. **Update test documentation**

### Example Migration

**Before:**
```
tests/test_backend_websocket_integration.py
```

**After:**
```
tests/backend/local/websocket/test_websocket_integration.py
```

**Import Update:**
```python
# Before
from tests.testing_utils.voice_encoder import encode_audio

# After
from tests.testing_utils.voice_encoder import encode_audio
# (No change needed - relative imports still work)
```

## Best Practices

1. **Keep tests organized** - Put tests in the correct directory
2. **Use descriptive names** - Make test purpose clear from filename
3. **Shared fixtures** - Use `conftest.py` for reusable fixtures
4. **Mock external services** - Use mocks for cloud services in local tests
5. **Clean test data** - Clean up created data after tests
6. **Document requirements** - List prerequisites in test docstrings
7. **Test independence** - Tests should not depend on each other
8. **Parallel execution** - Design tests to run in parallel safely

## Troubleshooting

### Import Errors
If you see import errors after moving tests:
```bash
# Ensure __init__.py exists in all test directories
find tests/ -type d -exec touch {}/__init__.py \;
```

### Path Issues
If tests can't find modules:
```python
# Add to top of test file
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
```

### Fixture Not Found
If pytest can't find fixtures:
1. Check `conftest.py` is in the correct location
2. Ensure fixture scope is appropriate
3. Verify import paths are correct

## Related Documentation

- [README.md](./README.md) - Main test documentation
- [voice_samples.json](./voice_samples/voice_samples.json) - Test data config
- [AUDIO_TESTING_GUIDE.md](./testing_utils/AUDIO_TESTING_GUIDE.md) - Audio testing guide
