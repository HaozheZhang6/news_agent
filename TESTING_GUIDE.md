# 🧪 Voice Agent Testing Guide

## Quick Start - One Button Test

### Step 1: Start the Backend Server

```bash
# In terminal 1
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the Makefile:
```bash
make run-server
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 2: Open the Voice Test Interface

**Option A: Double-click the file**
```bash
open voice_test.html
```

**Option B: Open in browser**
- Navigate to: `/Users/haozhezhang/Documents/Agents/News_agent/voice_test.html`
- Or drag the file to your browser

### Step 3: Test the Voice Interface

1. **Wait for Connection**: The page will automatically connect to the backend
2. **Grant Microphone Permission**: When prompted, click "Allow"
3. **Click the Big Microphone Button** 🎤
4. **Speak Your Request**: For example:
   - "Tell me the latest tech news"
   - "What's happening in the stock market?"
   - "Give me sports news"
5. **Click Again to Stop**: The agent will process your request
6. **Listen to Response**: Audio will stream back automatically

### What You'll See

**Status Indicators:**
- 🔴 **Red "Recording"** - Your microphone is active
- 🟢 **Green "Connected"** - Ready to use
- 🟡 **Yellow "Processing"** - Agent is thinking

**Conversation Flow:**
```
You: "Tell me the latest tech news"
  ↓
Agent: [Transcribes your speech]
  ↓
Agent: [Processes and fetches news]
  ↓
Agent: [Streams voice response]
  ↓
📰 News items displayed
```

---

## Advanced Testing Options

### Test 1: Simple Text Command (No Microphone)

Click **"Test Connection"** button to send a pre-written command without using your microphone.

### Test 2: WebSocket Protocol Testing

Use the original test file for detailed WebSocket debugging:
```bash
open test_websocket.html
```

This shows:
- Raw WebSocket messages
- Event types and payloads
- Chunk-by-chunk TTS streaming
- Error messages

### Test 3: API Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-10T..."
}
```

### Test 4: Direct API Testing

**Get Latest News:**
```bash
curl http://localhost:8000/api/news/latest?category=technology
```

**Test Voice Command (REST):**
```bash
curl -X POST http://localhost:8000/api/voice/command \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "command": "latest tech news",
    "confidence": 0.95
  }'
```

---

## Common Issues & Solutions

### ❌ "Connection error" or "Disconnected"

**Cause**: Backend not running

**Solution**:
```bash
# Check if backend is running
lsof -i :8000

# If not, start it
make run-server
```

### ❌ "Failed to access microphone"

**Cause**: Browser permissions not granted

**Solution**:
1. Click the 🔒 lock icon in address bar
2. Change microphone permission to "Allow"
3. Refresh the page

### ❌ No audio playback

**Cause**: Browser autoplay policy

**Solution**:
1. Click somewhere on the page first
2. Try recording again
3. Check browser console for errors (F12)

### ❌ Backend errors about missing environment variables

**Cause**: Environment variables not set

**Solution**:
```bash
# Create backend/.env file with:
ZHIPUAI_API_KEY=your_key_here
ALPHAVANTAGE_API_KEY=your_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_key
UPSTASH_REDIS_REST_URL=your_url
UPSTASH_REDIS_REST_TOKEN=your_token
```

Or use the env merger:
```bash
make env-merge
```

---

## Expected Backend Output

When working correctly, you should see logs like:

```
INFO:     WebSocket connection accepted
INFO:     Client connected: session_xyz123
INFO:     Received voice_data event
INFO:     Processing audio chunk (1024 bytes)
INFO:     Transcription: "tell me the latest tech news"
INFO:     Fetching news for category: technology
INFO:     Sending TTS chunk 1/5
INFO:     Streaming complete: 5 chunks sent
```

---

## Testing Checklist

- [ ] Backend server starts without errors
- [ ] Browser opens voice_test.html
- [ ] Status shows "Connected"
- [ ] Microphone button is clickable
- [ ] Recording starts (button turns red)
- [ ] Audio visualizer shows sound levels
- [ ] Transcript shows "Hearing: ..." while speaking
- [ ] Transcript shows your full text after stopping
- [ ] Agent response appears in transcript
- [ ] Audio plays back automatically
- [ ] News items display (if applicable)
- [ ] Can record multiple times in a row

---

## Architecture Overview

```
┌─────────────┐         WebSocket          ┌─────────────┐
│             │ ◄──────────────────────────►│             │
│   Browser   │    (Streaming Audio/Text)   │   Backend   │
│             │                              │   FastAPI   │
│  voice_test │         JSON Events:         │             │
│    .html    │   - voice_data               │ - Agent     │
│             │   - voice_command            │ - News API  │
│  🎤 Record  │   - transcription            │ - TTS       │
│  🔊 Play    │   - tts_chunk                │ - Cache     │
└─────────────┘   - streaming_complete       └─────────────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │   External APIs  │
                                          │                  │
                                          │ - ZhipuAI (LLM)  │
                                          │ - Alpha Vantage  │
                                          │ - Supabase       │
                                          │ - Upstash Redis  │
                                          └──────────────────┘
```

---

## Next Steps

Once basic testing works:

1. **Test with different queries**:
   - News categories (tech, sports, business)
   - Stock queries
   - Follow-up questions

2. **Test interruption handling**:
   - Start a recording
   - Click "Send Interrupt" in test_websocket.html

3. **Test memory/context**:
   - Ask for news
   - Then say "tell me more about the first one"

4. **Performance testing**:
   - Multiple rapid requests
   - Long recordings
   - Network throttling (Chrome DevTools)

5. **Mobile testing**:
   - Get local IP: `ifconfig | grep inet`
   - Access from phone: `http://YOUR_IP:8000`

---

**Happy Testing! 🚀**

