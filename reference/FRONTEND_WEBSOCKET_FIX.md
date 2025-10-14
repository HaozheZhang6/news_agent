# Frontend WebSocket Fix - In Progress

## Issue Identified

**Problem**: Frontend WebSocket connects but immediately disconnects

**Backend Error**:
```
INFO:     connection open
INFO:     connection closed
ERROR: WebSocketDisconnect
ERROR: Cannot call "send" once a close message has been sent
```

**Frontend Error**:
```
WS | Connecting to ws://localhost:8000/ws/voice?user_id=...
ERROR | WS | WebSocket error
ERROR | ❌ Error: Connection error. Please try again.
WS | Disconnected
```

## Root Cause

The frontend was automatically calling `startRecording()` immediately when receiving the "connected" event. This caused issues because:

1. **Microphone Permission Prompt**: When `getUserMedia()` is called, browser shows permission dialog
2. **Async Permission Flow**: While waiting for user permission, the WebSocket event loop continues
3. **Premature Closure**: If permission is denied or takes too long, or if there's any error, the WebSocket closes
4. **Backend Retry Loop**: Backend tries to send "connected" message but WebSocket is already closed

## Fix Applied

### Changes Made

#### File: `frontend/src/components/ContinuousVoiceInterface.tsx`

**1. Added Flag for Deferred Recording Start** (line 59):
```typescript
const shouldStartRecordingRef = useRef(false); // Flag to start recording after connection
```

**2. Updated "connected" Event Handler** (lines 121-130):
```typescript
case 'connected':
  sessionIdRef.current = message.data.session_id;
  logger.wsConnected(sessionIdRef.current);
  // If user clicked the button while connecting, start recording now
  if (shouldStartRecordingRef.current) {
    shouldStartRecordingRef.current = false;
    setVoiceState("listening");
    startRecording();
  }
  break;
```

**3. Updated startVoiceInteraction** (lines 454-466):
```typescript
const startVoiceInteraction = useCallback(async () => {
  // If not connected, open WS and set flag to start recording after connection
  if (!isConnected || !sessionIdRef.current) {
    setVoiceState("connecting");
    shouldStartRecordingRef.current = true; // Flag to start recording after connection
    connectWebSocket();
    return;
  }

  // Already connected with a valid session
  setVoiceState("listening");
  startRecording();
}, [isConnected, connectWebSocket, startRecording]);
```

## New Flow

### Before (Broken):
```
User clicks button
  → connectWebSocket()
  → WebSocket connects
  → Backend sends "connected" event
  → Frontend receives "connected"
  → Immediately calls startRecording()
  → getUserMedia() asks for mic permission
  → (While waiting) WebSocket closes somehow
  → Backend tries to send but connection closed
```

### After (Fixed):
```
User clicks button
  → Set shouldStartRecordingRef = true
  → connectWebSocket()
  → WebSocket connects
  → Backend sends "connected" event
  → Frontend receives "connected"
  → Checks shouldStartRecordingRef flag
  → If true, NOW start recording
  → getUserMedia() asks for permission
  → User grants permission
  → Recording starts successfully
```

## Benefits

1. **Stable Connection**: WebSocket stays open during microphone permission flow
2. **Better UX**: User sees "connecting" state clearly
3. **Error Isolation**: Microphone errors don't affect WebSocket
4. **Explicit Flow**: Recording only starts when explicitly requested by user action

## Testing Needed

### 1. WebSocket Connection Test
```bash
# Start backend
make run-server

# Open frontend
# Click microphone button
# Check browser console and backend logs
```

**Expected**:
- ✅ WebSocket connects successfully
- ✅ "Connected" event received
- ✅ No immediate disconnection
- ✅ Microphone permission prompt shows (if not granted before)
- ✅ After permission granted, recording starts

### 2. Error Handling Test
- ❌ User denies microphone permission → Should show error, keep WebSocket open
- ❌ No microphone available → Should show error gracefully
- ❌ Backend not running → Should show connection error

### 3. Full Pipeline Test (After connection works)
- Send audio to backend
- Receive transcription
- Receive agent response
- Receive and play TTS audio
- Test interruption when user speaks

## Known Issues to Fix

### 1. Callback Dependency Issue
```typescript
// Line 128: startRecording() might not be in closure
if (shouldStartRecordingRef.current) {
  shouldStartRecordingRef.current = false;
  setVoiceState("listening");
  startRecording(); // ⚠️ May not be available
}
```

**Solution**: Move `startRecording` call to effect or use a different pattern.

### 2. Audio Encoder Not Used
The component imports `useAudioEncoder` but never uses it:
```typescript
const audioEncoder = useAudioEncoder(userId); // Line 34 - unused
```

**Next Steps**: Implement audio encoding in `sendAudioToBackend()`.

### 3. WebM to OPUS Encoding
Current code records as `audio/webm;codecs=opus` but needs to send as base64 OPUS to match backend protocol.

## Next Implementation Steps

### 1. Fix startRecording Callback Issue ⏳
Update the handleWebSocketMessage to properly call startRecording.

### 2. Implement Audio Encoding ⏳
```typescript
const sendAudioToBackend = useCallback(async () => {
  if (audioChunksRef.current.length === 0) return;

  // Create audio blob from chunks
  const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });

  // Use audioEncoder to encode
  const encodedAudio = await audioEncoder.encodeAudioBlob(audioBlob);

  // Send to backend
  wsRef.current?.send(JSON.stringify({
    event: 'audio_chunk',
    data: {
      audio_chunk: encodedAudio.audio_chunk, // base64
      format: 'opus',
      is_final: true
    }
  }));

  // Clear chunks for next recording
  audioChunksRef.current = [];
}, [audioEncoder]);
```

### 3. Test TTS Audio Playback ⏳
Ensure the `handleTTSChunk` function properly decodes and plays MP3 audio from backend.

### 4. Test VAD (Voice Activity Detection) ⏳
Verify that:
- Speech detection works (SPEECH_THRESHOLD = 0.01)
- Silence detection triggers send after 1 second
- Interruption works when user speaks during agent response

## Backend Protocol Reference

### Frontend → Backend

**audio_chunk**:
```json
{
  "event": "audio_chunk",
  "data": {
    "audio_chunk": "<base64-opus>",
    "format": "opus",
    "is_final": true
  }
}
```

**interrupt**:
```json
{
  "event": "interrupt",
  "data": {
    "session_id": "<uuid>",
    "reason": "user_started_speaking"
  }
}
```

### Backend → Frontend

**connected**:
```json
{
  "event": "connected",
  "data": {
    "session_id": "<uuid>",
    "message": "Connected to Voice News Agent",
    "timestamp": "2025-10-12..."
  }
}
```

**transcription**:
```json
{
  "event": "transcription",
  "data": {
    "text": "what's the latest news about nvidia",
    "timestamp": "..."
  }
}
```

**agent_response**:
```json
{
  "event": "agent_response",
  "data": {
    "text": "Here are some of the latest...",
    "timestamp": "..."
  }
}
```

**tts_chunk**:
```json
{
  "event": "tts_chunk",
  "data": {
    "audio_chunk": "<base64-mp3>",
    "chunk_index": 0,
    "format": "mp3",
    "timestamp": "..."
  }
}
```

**streaming_complete**:
```json
{
  "event": "streaming_complete",
  "data": {
    "total_chunks": 24,
    "timestamp": "..."
  }
}
```

## Files Modified

1. ✅ `frontend/src/components/ContinuousVoiceInterface.tsx`
   - Added `shouldStartRecordingRef` flag
   - Updated "connected" event handler
   - Updated `startVoiceInteraction` to set flag

## Files to Create/Update Next

1. ⏳ Fix callback closure issue in handleWebSocketMessage
2. ⏳ Implement audio encoding in sendAudioToBackend
3. ⏳ Test and fix audio playback
4. ⏳ Test VAD functionality
5. ⏳ Create comprehensive testing guide

## Status

**WebSocket Connection**: 🔄 In Progress - needs testing
**Audio Recording**: ⏳ Pending - needs callback fix
**Audio Encoding**: ⏳ Pending - needs implementation
**Audio Playback**: ⏳ Pending - needs testing
**VAD**: ⏳ Pending - needs testing
**Full Pipeline**: ⏳ Pending - awaiting above fixes

---

**Date**: October 12, 2025
**Status**: 🔄 In Progress
**Next**: Test WebSocket connection stability
