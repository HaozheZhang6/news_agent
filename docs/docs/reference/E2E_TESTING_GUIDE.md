# End-to-End Testing Guide

Complete guide for running full integration tests with both frontend and backend.

## Table of Contents

- [Quick Start](#quick-start)
- [Automated E2E Testing](#automated-e2e-testing)
- [Manual E2E Testing](#manual-e2e-testing)
- [Test Components](#test-components)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Option 1: Automated Script (Recommended)

```bash
# Run full E2E test suite (starts both servers + runs tests)
./tests/e2e/run_e2e_tests.sh
```

### Option 2: Makefile Target

```bash
# Add to your Makefile and run
make test-e2e
```

### Option 3: Manual Testing

```bash
# Terminal 1: Start backend
make run-server

# Terminal 2: Start frontend
make run-frontend

# Terminal 3: Run tests
uv run pytest tests/integration/ -v
```

---

## Automated E2E Testing

### Using the E2E Test Runner

The `run_e2e_tests.sh` script handles everything automatically:

```bash
cd /path/to/News_agent
./tests/e2e/run_e2e_tests.sh
```

**What it does**:
1. ✅ Checks dependencies (uv, npm)
2. ✅ Starts backend on port 8000
3. ✅ Waits for backend health check
4. ✅ Starts frontend on port 3000
5. ✅ Waits for frontend to be ready
6. ✅ Runs backend E2E tests
7. ✅ Keeps servers running for manual testing
8. ✅ Cleans up on exit (Ctrl+C)

**Output Example**:
```
═══════════════════════════════════════════════════
   Voice News Agent - End-to-End Test Runner
═══════════════════════════════════════════════════

Checking dependencies...
✓ All dependencies found

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1: Starting Backend Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Starting backend on port 8000...
  Logs: /tmp/e2e_backend.log
  Backend PID: 12345
  Waiting for backend to be ready.........
✓ Backend is ready!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Starting Frontend Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Starting frontend on port 3000...
  Logs: /tmp/e2e_frontend.log
  Frontend PID: 12346
  Waiting for frontend to be ready.....................
✓ Frontend is ready!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Running Backend E2E Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

test_complete_voice_interaction PASSED
test_vad_rejection_flow PASSED
test_interruption_during_response PASSED

✓ Backend E2E tests passed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: Manual Testing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Both servers are running!

  Frontend: http://localhost:3000
  Backend:  http://localhost:8000
  API Docs: http://localhost:8000/docs
  Health:   http://localhost:8000/health

Manual Test Checklist:
  1. Open frontend in browser
  2. Click the microphone button
  3. Speak a question (e.g., 'What is the price of Apple?')
  4. Wait for agent response
  5. While agent is speaking, interrupt by speaking again
  6. Verify agent stops and processes your interruption

Logs:
  Backend:  tail -f /tmp/e2e_backend.log
  Frontend: tail -f /tmp/e2e_frontend.log

Press Ctrl+C to stop servers and exit
```

---

## Manual E2E Testing

### Step-by-Step Manual Testing

#### 1. Start Backend

```bash
# Terminal 1
cd /path/to/News_agent
make run-server

# Or with uv directly
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Health Check**:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

#### 2. Start Frontend

```bash
# Terminal 2
cd /path/to/News_agent
make run-frontend

# Or with npm directly
cd frontend
npm run dev
```

**Expected Output**:
```
  VITE v5.0.0  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

#### 3. Run Integration Tests

```bash
# Terminal 3
cd /path/to/News_agent

# Run all integration tests
uv run pytest tests/integration/ -v -s

# Run specific E2E test
uv run pytest tests/integration/test_e2e_vad_interruption.py -v -s

# Run with specific test
uv run pytest tests/integration/test_e2e_vad_interruption.py::TestE2EVADInterruption::test_complete_voice_interaction -v -s
```

#### 4. Manual Browser Testing

1. **Open Frontend**: http://localhost:3000
2. **Test Basic Voice**:
   - Click microphone button
   - Speak: "What is the price of Apple?"
   - Wait for response
   - Verify audio playback

3. **Test Interruption**:
   - Click microphone and speak
   - While agent is responding, start speaking again
   - Agent should stop immediately
   - Your new question should be processed

4. **Test VAD**:
   - Click microphone
   - Speak very quietly → Should be rejected if energy too low
   - Speak normally → Should be accepted
   - Check browser console and backend logs

---

## Test Components

### Backend E2E Tests

**Location**: `tests/integration/test_e2e_vad_interruption.py`

**Tests**:
1. `test_complete_voice_interaction` - Full voice flow
2. `test_vad_rejection_flow` - VAD rejection handling
3. `test_interruption_during_response` - Interruption while agent speaks
4. `test_multiple_audio_chunks_sequence` - Conversation flow
5. `test_end_to_end_latency` - Performance testing
6. `test_invalid_audio_format` - Error handling

**Run specific test**:
```bash
uv run pytest tests/integration/test_e2e_vad_interruption.py::TestE2EVADInterruption::test_interruption_during_response -v -s
```

### Frontend Testing

**Manual Test Checklist**:

```
□ Voice Input
  □ Click microphone button
  □ Microphone permission granted
  □ Recording indicator shows
  □ VAD detects speech
  □ Audio sent to backend

□ Agent Response
  □ Transcription displayed
  □ Agent response text shown
  □ Audio playback starts
  □ Speaking indicator visible

□ Interruption
  □ Can interrupt during speech
  □ Audio stops immediately
  □ New question processed
  □ UI updates correctly

□ VAD Behavior
  □ VAD active during listening
  □ VAD active during agent speech
  □ VAD detects quiet speech
  □ VAD rejects silence

□ Error Handling
  □ Microphone permission denied
  □ Network error
  □ Backend timeout
  □ Invalid audio format
```

---

## Configuration

### Backend Configuration

**File**: `backend/.env`

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# VAD Settings (for E2E testing)
VAD_ENERGY_THRESHOLD=500.0
VAD_SPEECH_RATIO_THRESHOLD=0.03
VAD_AGGRESSIVENESS=3

# ASR (Use HF Space for faster testing)
USE_LOCAL_ASR=false
HF_SPACE_NAME=hz6666/SenseVoiceSmall
```

### Frontend Configuration

**File**: `frontend/.env`

```bash
# Backend URL
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# VAD Settings
VITE_VAD_THRESHOLD=0.5
VITE_SILENCE_TIMEOUT=1500
```

---

## Troubleshooting

### Backend Won't Start

**Issue**: Port 8000 already in use
```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
lsof -ti:8000 | xargs kill -9

# Restart backend
make run-server
```

**Issue**: Database connection failed
```bash
# Check Supabase credentials
cat env_files/supabase.env

# Test connection
curl -H "apikey: YOUR_KEY" "YOUR_SUPABASE_URL/rest/v1/"
```

### Frontend Won't Start

**Issue**: Port 3000 already in use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Restart frontend
cd frontend && npm run dev
```

**Issue**: Dependencies not installed
```bash
cd frontend
npm install
npm run dev
```

### Tests Failing

**Issue**: Connection refused
- Ensure backend is running: `curl http://localhost:8000/health`
- Ensure frontend is running: `curl http://localhost:3000`
- Check firewall settings

**Issue**: VAD rejecting audio
```bash
# Check VAD settings
grep "VAD_" backend/.env

# Lower thresholds for testing
export VAD_SPEECH_RATIO_THRESHOLD=0.01
export VAD_ENERGY_THRESHOLD=300.0
```

**Issue**: Timeout errors
- Increase test timeouts in pytest
- Check network latency
- Verify ASR service (HF Space) is accessible

### WebSocket Issues

**Issue**: WebSocket connection fails
```bash
# Test WebSocket endpoint
wscat -c ws://localhost:8000/ws/voice/test-session-id

# Check CORS settings
grep CORS backend/.env
```

**Issue**: Messages not received
- Check browser console for errors
- Verify WebSocket events in Network tab
- Check backend logs for WebSocket errors

---

## Performance Benchmarks

Expected E2E performance:

| Metric | Target | Acceptable |
|--------|--------|------------|
| Backend Startup | < 3s | < 5s |
| Frontend Startup | < 10s | < 20s |
| Health Check | < 100ms | < 500ms |
| Voice → Transcription | < 2s | < 5s |
| Transcription → Response | < 1s | < 3s |
| Response → TTS Start | < 500ms | < 1s |
| Interrupt Latency | < 100ms | < 500ms |
| Full E2E (Voice → Audio) | < 5s | < 10s |

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Setup Node
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: |
          uv pip install -r requirements.txt
          cd frontend && npm install

      - name: Run E2E tests
        run: ./tests/e2e/run_e2e_tests.sh
        timeout-minutes: 10
```

---

## Advanced Testing

### Load Testing

```bash
# Install locust
uv pip install locust

# Run load test
locust -f tests/load/test_voice_load.py --host=http://localhost:8000
```

### Stress Testing WebSocket

```python
# tests/stress/test_websocket_concurrent.py
import asyncio
import websockets

async def test_concurrent_connections():
    tasks = []
    for i in range(100):
        tasks.append(connect_and_test(f"session-{i}"))

    await asyncio.gather(*tasks)
```

---

## Quick Reference

### Commands

```bash
# Start servers
make run-server          # Backend
make run-frontend        # Frontend

# Run tests
./tests/e2e/run_e2e_tests.sh # Automated E2E
uv run pytest tests/integration/ -v  # Backend tests only

# Check status
curl http://localhost:8000/health    # Backend health
curl http://localhost:3000           # Frontend

# View logs
tail -f /tmp/e2e_backend.log
tail -f /tmp/e2e_frontend.log

# Stop servers
pkill -f uvicorn         # Stop backend
pkill -f vite            # Stop frontend
```

### URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws/voice/{session_id}

---

## Related Documentation

- [VAD Testing Guide](VAD_TESTING_GUIDE.md) - VAD-specific tests
- [VAD Configuration](VAD_CONFIG_GUIDE.md) - VAD settings
- [API Documentation](http://localhost:8000/docs) - Backend API docs
- [Frontend README](frontend/README.md) - Frontend setup

---

**Last Updated**: 2025-10-16
**Test Framework Version**: v1.0
