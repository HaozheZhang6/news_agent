# 🧪 Pre-Commit Testing Checklist

Run these tests before committing the native Python deployment changes.

## ✅ Backend Tests

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected:** `status: "unhealthy"` or `"healthy"` (database can be unhealthy, but websocket should be healthy)

**Result:** ✅ WebSocket is healthy, cache is healthy

---

### 2. API Documentation
```bash
open http://localhost:8000/docs
```

**Expected:** Swagger UI opens with all endpoints

---

### 3. News API Test
```bash
curl 'http://localhost:8000/api/news/latest?category=technology'
```

**Expected:** JSON response with news articles (or empty array if cache/API limits)

**Result:** ✅ Returns valid JSON response

---

## 🎤 Voice Interface Tests

### Test 1: WebSocket Connection Test

```bash
open test_websocket.html
```

**Steps:**
1. Click "Connect" button
2. Wait for "Connected" status
3. Click "Send Voice Command"
4. Check messages log for responses

**Expected:**
- ✅ Connection established
- ✅ Session ID received
- ✅ Voice command sent
- ✅ Response received

---

### Test 2: Voice Recording Test (Main Interface)

```bash
open voice_test.html
```

**Steps:**
1. Wait for "Connected - Ready to talk!" status
2. Click the big microphone button (turns red)
3. Speak: "Tell me the latest tech news"
4. Click button again to stop (turns purple)
5. Wait for response

**Expected:**
- ✅ Status shows "Connected"
- ✅ Button clickable (not grayed out)
- ✅ Recording starts (red button, visualizer animates)
- ✅ Recording stops (purple button)
- ✅ Transcription appears in transcript box
- ✅ Agent response appears
- ✅ Audio plays back (if TTS working)

---

## 🔍 Configuration Tests

### 1. Check render.yaml syntax

```bash
cat render.yaml
```

**Verify:**
- ✅ `runtime: python3` (NOT `env: docker`)
- ✅ `rootDir: backend`
- ✅ `buildCommand` references `../requirements.txt`
- ✅ `startCommand` uses uvicorn with `$PORT`
- ✅ `PYTHON_VERSION: 3.11.0`

---

### 2. Verify Docker removed

```bash
# Should NOT exist
ls backend/Dockerfile 2>&1

# Should NOT contain docker commands
grep -i "docker-build\|docker-run" Makefile
```

**Expected:**
- ❌ Dockerfile not found
- ❌ No docker commands in Makefile

---

### 3. Check documentation updated

```bash
# Should NOT contain Docker references
grep -c "Docker\|docker" README.md MVP.md STREAMING_AND_DEPLOYMENT.md
```

**Expected:** Minimal Docker references (only historical context)

---

## 🚀 Render Deployment Simulation

### 1. Simulate build command

```bash
cd backend
pip install --upgrade pip
pip install -r ../requirements.txt
```

**Expected:** All packages install successfully

---

### 2. Simulate start command

```bash
cd backend
PORT=8000 uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

**Expected:** Server starts on port 8000

---

## 📊 Test Results Summary

Fill in after testing:

- [ ] Backend health check: PASS / FAIL
- [ ] API docs accessible: PASS / FAIL
- [ ] News API working: PASS / FAIL
- [ ] WebSocket connection: PASS / FAIL
- [ ] Voice recording: PASS / FAIL
- [ ] Audio playback: PASS / FAIL
- [ ] render.yaml valid: PASS / FAIL
- [ ] Docker removed: PASS / FAIL
- [ ] Docs updated: PASS / FAIL
- [ ] Build command works: PASS / FAIL

---

## ✅ Ready to Commit When:

- [x] Backend is healthy (WebSocket + Cache at minimum)
- [x] render.yaml uses native Python (no Docker)
- [x] Docker files removed
- [x] Documentation updated
- [ ] WebSocket test passes
- [ ] Voice interface connects

---

## 🎯 Quick Test Command

Run all tests at once:

```bash
# Test backend
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ Backend OK" || echo "⚠️  Backend issue"

# Test WebSocket
curl -s http://localhost:8000/docs > /dev/null && echo "✅ API docs OK" || echo "❌ API docs failed"

# Check Docker removed
[ ! -f backend/Dockerfile ] && echo "✅ Docker removed" || echo "❌ Docker still exists"

# Check render.yaml
grep -q "runtime: python3" render.yaml && echo "✅ Native Python config" || echo "❌ Still using Docker"

# Open tests
echo "Opening test interfaces..."
open test_websocket.html
open voice_test.html
```

---

**After all tests pass, commit with:**

```bash
git add -A
git commit -m "refactor: Switch from Docker to native Python deployment"
git push origin main
```

