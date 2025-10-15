# Frontend Logging System - Complete Guide

## Overview

The frontend now has **comprehensive logging** that captures:
- ✅ Application lifecycle (startup, shutdown)
- ✅ Page navigation
- ✅ All HTTP API requests and responses
- ✅ WebSocket connections and messages
- ✅ User interactions (button clicks, commands)
- ✅ Voice state changes (idle, listening, speaking)
- ✅ Audio events (VAD, chunks sent/received)
- ✅ Toast notifications (success, error, warning, info)
- ✅ Unhandled errors and promise rejections
- ✅ React component errors (via ErrorBoundary)

---

## What Gets Logged

### 1. Application Lifecycle
```typescript
✅ App started
✅ Environment (development/production)
✅ User Agent (browser info)
✅ App shutdown
✅ Unhandled errors
✅ Unhandled promise rejections
```

### 2. Navigation
```typescript
✅ Page changes (dashboard, profile, history)
✅ Auth view changes (login, register, admin)
```

### 3. HTTP API Requests
```typescript
📤 HTTP GET /api/user/watchlist
   - URL: http://localhost:8000/api/user/watchlist?user_id=XXX
   - Params: {user_id: "XXX"}

📥 HTTP GET /api/user/watchlist success
   - Status: 200
   - Duration: 300ms
   - Data size: 123 bytes
```

### 4. WebSocket Communication
```typescript
🔌 WS_CONNECT | url=ws://localhost:8000/ws/voice?user_id=XXX
ℹ️ INFO | ws | WebSocket connection opened
📥 WS_RECV | event=connected | session=XXX
🎯 WS_CONNECTED | session=XXX
📤 WS_SEND | event=audio_chunk | session=XXX
📥 WS_RECV | event=transcription | session=XXX
📝 TRANSCRIPTION | text='What is the stock price...'
📥 WS_RECV | event=agent_response | session=XXX
🤖 RESPONSE | text='The current stock price...'
🔌 WS_DISCONNECT
```

### 5. Voice Activity Detection (VAD)
```typescript
🎤 VAD_SEND_TRIGGERED
📤 AUDIO_CHUNK_SENT | size=12345 | session=XXX
📤 WS_SEND | event=audio_chunk | session=XXX
🔊 TTS_CHUNK_RECEIVED | index=0
🔊 TTS_CHUNK_PLAYED | index=0
🚨 INTERRUPTION (when user speaks while agent is talking)
```

### 6. User Interactions
```typescript
🖱️ Profile button clicked
🖱️ Conversation history button clicked
🖱️ Logout button clicked
🖱️ Quick command clicked: Latest News
```

### 7. State Changes
```typescript
🔄 Voice state changed: idle → listening
🔄 Voice state changed: listening → speaking
🔄 Voice state changed: speaking → listening
🔄 Connection state changed: disconnected → connected
```

### 8. Toast Notifications
```typescript
✅ Success: Data saved successfully
❌ Error: Connection failed
⚠️ Warning: Session expiring soon
ℹ️ Info: Quick command: Latest News
⏳ Loading: Fetching data...
```

### 9. Errors
```typescript
❌ React Error Boundary caught error
   - Error: Cannot read property 'X' of undefined
   - Stack: (full stack trace)
   - Component: (component stack)

❌ Unhandled error
   - Message: Script error
   - Filename: app.tsx
   - Line: 123
   - Column: 45

❌ Unhandled promise rejection
   - Reason: Network request failed

❌ HTTP GET /api/news failed
   - Status: 500
   - StatusText: Internal Server Error
   - Duration: 1234ms
```

---

## How to View Logs

### Method 1: Browser Console (Real-time)
1. Open browser at http://localhost:3000
2. Press F12 (or Cmd+Option+I on Mac)
3. Go to Console tab
4. See color-coded logs in real-time

**Console Output Example:**
```
🚀 APP | Voice News Agent application started
ℹ️ APP | Environment: development
📤 API | HTTP GET /api/user/watchlist
📥 API | HTTP GET /api/user/watchlist success (300ms)
🔌 WS | WS_CONNECT | url=ws://localhost:8000/ws/voice?user_id=XXX
🎯 WS | WS_CONNECTED | session=XXX
```

### Method 2: Log Viewer Modal
1. Open browser at http://localhost:3000
2. Click "View Logs" button (bottom-right corner)
3. See all logs in a scrollable modal
4. Click "Download" to save logs
5. Click "Clear" to clear logs

### Method 3: Download Logs
1. Click "Download Logs" button (bottom-right corner)
2. File saved as: `frontend_{YYYYMMDD}_{HHMMSS}.log`
3. Location: Your browser's Downloads folder
4. Format: JSON array of log entries

### Method 4: localStorage
Logs are automatically saved to browser's localStorage:
```javascript
// In browser console:
localStorage.getItem('frontend_log_session') // Get session timestamp
localStorage.getItem('voice_agent_logs_YYYYMMDD_HHMMSS') // Get logs
```

---

## Log Entry Structure

Each log entry contains:
```typescript
{
  "timestamp": "2025-10-11T23:42:30.123Z",
  "level": "info" | "debug" | "warn" | "error",
  "category": "app" | "api" | "ws" | "ui" | "state" | "toast" | "navigation",
  "message": "Human-readable message",
  "data": {
    // Optional additional data
  }
}
```

---

## What Gets Logged (Comprehensive List)

### ✅ Application Events
- [x] App startup
- [x] App shutdown
- [x] Environment info
- [x] Browser info
- [x] Unhandled errors
- [x] Unhandled promise rejections
- [x] React component errors

### ✅ Navigation Events
- [x] Page navigation (dashboard, profile, history)
- [x] Auth view changes (login, register, admin)

### ✅ HTTP API Events
- [x] Request sent (method, URL, params, body)
- [x] Response received (status, duration, data size)
- [x] Request failed (error message, duration)
- [x] Network errors (timeout, connection refused)

### ✅ WebSocket Events
- [x] Connection initiated
- [x] Connection opened
- [x] Connection closed
- [x] Connection error
- [x] Message sent (event type, session ID)
- [x] Message received (event type, session ID)
- [x] Connected event (session ID assigned)
- [x] Transcription received
- [x] Agent response received
- [x] TTS chunks received
- [x] Streaming complete
- [x] Streaming interrupted

### ✅ Voice Events
- [x] VAD send triggered (silence detected)
- [x] Audio chunk sent (size, session ID)
- [x] TTS chunk received (index)
- [x] TTS chunk played (index)
- [x] Interruption triggered
- [x] Audio playback stopped

### ✅ UI Events
- [x] Button clicks (profile, history, logout)
- [x] Quick command clicks
- [x] Mic button clicks (start/stop)
- [x] Mute button clicks

### ✅ State Changes
- [x] Voice state changes (idle, listening, speaking, connecting)
- [x] Connection state changes (connected, disconnected)

### ✅ Toast Notifications
- [x] Success messages
- [x] Error messages
- [x] Warning messages
- [x] Info messages
- [x] Loading messages
- [x] Promise-based toasts (loading → success/error)

---

## Testing Your Logging System

### Test 1: Basic Application Startup
1. Open http://localhost:3000
2. Open browser console (F12)
3. **Expected logs:**
   ```
   🚀 APP | Voice News Agent application started
   ℹ️ APP | Environment: development
   ℹ️ APP | User Agent: Mozilla/5.0...
   ℹ️ NAVIGATION | Viewing auth page: login
   ```

### Test 2: Navigation
1. Click "Profile" button
2. **Expected log:**
   ```
   🖱️ UI | Profile button clicked
   ℹ️ NAVIGATION | Navigated to page: profile
   ```

### Test 3: HTTP API Request
1. (Assuming you're logged in and on dashboard)
2. Page should auto-fetch watchlist
3. **Expected logs:**
   ```
   📤 API | HTTP GET /api/user/watchlist
   📥 API | HTTP GET /api/user/watchlist success | status=200 | duration=300ms
   ```

### Test 4: WebSocket Connection
1. Click the mic button (to start voice interface)
2. **Expected logs:**
   ```
   🔌 WS | WS_CONNECT | url=ws://localhost:8000/ws/voice?user_id=XXX
   ℹ️ WS | WebSocket connection opened
   📥 WS | WS_RECV | event=connected | session=XXX
   🎯 WS | WS_CONNECTED | session=XXX
   🔄 STATE | Voice state changed: listening
   ```

### Test 5: Voice Activity Detection
1. With mic active, speak into microphone
2. Stop speaking for 1 second
3. **Expected logs:**
   ```
   🎤 VAD | VAD_SEND_TRIGGERED
   📤 AUDIO | AUDIO_CHUNK_SENT | size=12345 | session=XXX
   📤 WS | WS_SEND | event=audio_chunk | session=XXX
   📥 WS | WS_RECV | event=transcription | session=XXX
   📝 TRANSCRIPTION | text='your speech'
   📥 WS | WS_RECV | event=agent_response | session=XXX
   🤖 RESPONSE | text='agent response'
   🔊 TTS | TTS_CHUNK_RECEIVED | index=0
   🔊 TTS | TTS_CHUNK_PLAYED | index=0
   ```

### Test 6: Toast Notification
1. Click a quick command button
2. **Expected logs:**
   ```
   🖱️ UI | Quick command clicked: Latest News
   ℹ️ TOAST | ℹ️ Info: Quick command: Latest News
   ```

### Test 7: Error Handling
1. Simulate a connection error (disconnect backend)
2. Try clicking mic button
3. **Expected logs:**
   ```
   ❌ WS | WS_ERROR | error=...
   ❌ TOAST | ❌ Error: Connection error. Please try again.
   ```

### Test 8: Download Logs
1. Click "Download Logs" button (bottom-right)
2. Check Downloads folder
3. Open `frontend_YYYYMMDD_HHMMSS.log`
4. Verify it contains JSON array of all logs

---

## Comparison: Before vs After

### Before (No Logging)
❌ Empty log files
❌ No visibility into user actions
❌ No HTTP request/response tracking
❌ No WebSocket message tracking
❌ No error tracking
❌ No state change tracking
❌ No way to debug issues

### After (Comprehensive Logging)
✅ Every action logged
✅ Every HTTP request/response logged
✅ Every WebSocket message logged
✅ Every error captured
✅ Every state change tracked
✅ Easy debugging with log viewer
✅ Downloadable logs for support

---

## Log Viewer Features

### View Logs Modal
- 📋 See all logs in chronological order
- 🔍 Scroll through thousands of entries
- 💾 Download logs to file
- 🗑️ Clear logs from storage
- ❌ Close modal to continue using app

### Download Format
```json
[
  {
    "timestamp": "2025-10-11T23:42:30.123Z",
    "level": "info",
    "category": "app",
    "message": "Voice News Agent application started"
  },
  {
    "timestamp": "2025-10-11T23:42:30.456Z",
    "level": "info",
    "category": "api",
    "message": "📤 HTTP GET /api/user/watchlist",
    "data": {
      "url": "http://localhost:8000/api/user/watchlist?user_id=test123",
      "params": {"user_id": "test123"}
    }
  },
  ...
]
```

---

## Troubleshooting

### "Logs are empty"
**Cause**: Logger not initialized or no actions taken yet
**Solution**: 
1. Refresh the page
2. Take some actions (click buttons, navigate, etc.)
3. Check console for real-time logs
4. If console shows logs but download is empty, check browser localStorage

### "Download button doesn't work"
**Cause**: Browser blocking downloads or no logs yet
**Solution**:
1. Check browser console for errors
2. Ensure you've taken some actions to generate logs
3. Try viewing logs in modal first
4. Check browser's download settings

### "Too many logs"
**Cause**: Debug-level logs filling up storage
**Solution**:
- Logs auto-cap at 1000 entries (oldest removed first)
- Click "Clear" in log viewer to reset
- Download and clear regularly for long sessions

---

## Summary

Your frontend logging system is now **production-ready** and captures:

1. ✅ **Application lifecycle** - startup, shutdown, errors
2. ✅ **Navigation** - every page and view change
3. ✅ **HTTP requests** - method, URL, params, response, duration
4. ✅ **WebSocket** - connect, disconnect, all messages
5. ✅ **Voice pipeline** - VAD, audio chunks, transcriptions, TTS
6. ✅ **User interactions** - every button click and command
7. ✅ **State changes** - voice state, connection state
8. ✅ **Toast notifications** - all success/error/warning messages
9. ✅ **Errors** - unhandled errors, promise rejections, React errors

**No more empty logs!** 🎉

Every user interaction, API call, WebSocket message, and error is now captured and easily accessible for debugging and monitoring.

