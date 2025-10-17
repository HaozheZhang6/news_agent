# E2E Testing - Quick Start

Quick reference for running end-to-end tests.

## 🚀 One Command (Recommended)

```bash
make test-e2e
```

Or directly:

```bash
./tests/e2e/run_e2e_tests.sh
```

**This will**:
- ✅ Start backend automatically
- ✅ Start frontend automatically
- ✅ Run automated tests
- ✅ Keep servers running for manual testing
- ✅ Clean up on exit (Ctrl+C)

---

## 📋 Manual Testing (3 Terminals)

### Terminal 1: Backend
```bash
make run-server
# Wait for: "Uvicorn running on http://0.0.0.0:8000"
```

### Terminal 2: Frontend
```bash
make run-frontend
# Wait for: "Local: http://localhost:3000/"
```

### Terminal 3: Tests
```bash
# Run all E2E tests
uv run pytest tests/integration/ -v

# Run specific test
uv run pytest tests/integration/test_e2e_vad_interruption.py::TestE2EVADInterruption::test_complete_voice_interaction -v
```

---

## 🧪 Test Types

### Full E2E Test
```bash
make test-e2e
```

### VAD Tests Only
```bash
make test-vad
# Or
python tests/run_vad_tests.py --vad-only
```

### Backend Integration Tests
```bash
make test-integration
```

### All Tests
```bash
make run-tests
```

---

## 🌐 Access Points

Once servers are running:

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Health** | http://localhost:8000/health |
| **WebSocket** | ws://localhost:8000/ws/voice/{session_id} |

---

## ✅ Manual Test Checklist

1. **Basic Voice**:
   - [ ] Click microphone
   - [ ] Speak: "What is the price of Apple?"
   - [ ] Agent responds with audio

2. **Interruption**:
   - [ ] While agent speaks, start talking
   - [ ] Agent stops immediately
   - [ ] New question processed

3. **VAD**:
   - [ ] Speak quietly → Check if detected
   - [ ] Speak normally → Should be accepted
   - [ ] Check logs for VAD ACCEPTED messages

---

## 🛑 Stop Servers

```bash
# Clean stop
Ctrl+C  # In the terminal running run_e2e_tests.sh

# Force stop
make stop-servers

# Manual
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

---

## 📝 View Logs

### During Automated Tests
```bash
# Backend
tail -f /tmp/e2e_backend.log

# Frontend
tail -f /tmp/e2e_frontend.log
```

### During Manual Testing
```bash
# Backend logs (in Terminal 1 running make run-server)
# Frontend logs (in Terminal 2 running make run-frontend)
```

---

## 🐛 Troubleshooting

### "Port already in use"
```bash
make stop-servers
# Then restart
```

### "Tests failing"
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check VAD settings
grep "VAD_" backend/.env
```

### "WebSocket errors"
```bash
# Test WebSocket directly
wscat -c ws://localhost:8000/ws/voice/test-123

# Check CORS
grep CORS backend/.env
```

---

## 📚 Full Documentation

See [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md) for:
- Detailed setup instructions
- Configuration options
- Advanced testing
- CI/CD integration
- Performance benchmarks

---

## ⚡ Quick Commands Reference

```bash
# Start/Stop
make run-server          # Start backend
make run-frontend        # Start frontend
make stop-servers        # Stop all servers

# Test
make test-e2e            # Full E2E test
make test-vad            # VAD tests only
make test-integration    # Backend integration
make run-tests           # All tests

# Check
curl http://localhost:8000/health    # Backend
curl http://localhost:3000           # Frontend

# Logs
tail -f /tmp/e2e_backend.log
tail -f /tmp/e2e_frontend.log
```

---

**Quick Start Time**: ~30 seconds (automated) or ~2 minutes (manual)

**Need help?** See [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)
