# 🧪 Local Testing Guide

## Quick Start - Talk with Your Agent in 3 Steps!

### Step 1: Start the Backend Server

```bash
# Option A: Use the startup script (easiest)
./START_TEST.sh

# Option B: Manual start
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on **http://localhost:8000**

### Step 2: Open the Test Interface

Open one of these files in your browser:

**🎤 Voice Test (with microphone):**
```bash
open test_voice_simple.html
```
- Click "Connect"
- Click the big microphone button 🎤
- Speak your command
- Click again to stop and send

**⌨️ Text Test (simpler, no mic needed):**
```bash
open test_websocket.html
```
- Click "Connect"  
- Type command in the text box
- Click "Send Voice Command"

### Step 3: Try These Commands

- "Tell me the latest news"
- "Latest tech news"
- "Add Apple to my watchlist"
- "Tell me more"
- "Stock news"

---

## What You Should See

### 1. Backend Server Running
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 2. Test Page Connected
```
✅ Connected! (Session: abc123...)
```

### 3. Agent Response
```
🤖 Response: "Here are the latest news headlines..."
📰 News items: 5
🎵 TTS streaming starting...
```

---

## Troubleshooting

### ❌ "WebSocket error - is the server running?"
**Fix:** Make sure the backend is running on port 8000
```bash
./START_TEST.sh
```

### ❌ "Microphone error: Permission denied"
**Fix:** Allow microphone access in your browser:
- Chrome/Edge: Settings → Privacy → Microphone
- Safari: System Preferences → Security & Privacy → Microphone
- Or just use the text test instead!

### ❌ "Error processing voice command"
**Fix:** Check your backend/.env has these keys:
```bash
cat backend/.env | grep API_KEY
```
You need at least `ZHIPUAI_API_KEY` for the agent to work.

### ❌ "Module not found" errors
**Fix:** Install dependencies:
```bash
pip install -r requirements.txt
```

---

## API Documentation

Once the server is running, visit:
- **Interactive API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## Advanced Testing

### Test with curl
```bash
# Health check
curl http://localhost:8000/health

# Text command (no WebSocket)
curl -X POST "http://localhost:8000/api/voice/command" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "latest tech news",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

### Test with Python
```python
import asyncio
import websockets
import json

async def test_agent():
    uri = "ws://localhost:8000/ws/voice?user_id=test_user"
    async with websockets.connect(uri) as websocket:
        # Wait for connection
        response = await websocket.recv()
        data = json.loads(response)
        session_id = data['data']['session_id']
        
        # Send command
        await websocket.send(json.dumps({
            "event": "voice_command",
            "data": {
                "session_id": session_id,
                "command": "latest tech news",
                "confidence": 0.95
            }
        }))
        
        # Get response
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(test_agent())
```

---

## Next Steps

1. ✅ Test locally with the HTML interface
2. ✅ Verify API responses in the logs
3. ✅ Test different commands and scenarios
4. 🚀 Deploy to Render when ready
5. 📱 Integrate with iOS app

---

**Happy Testing! 🎉**

