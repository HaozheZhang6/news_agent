# Critical Fixes Needed

## Root Cause of Current Issue

**Problem**: Frontend sends WebSocket messages (audio_chunk, interrupt) BEFORE backend has sent the 'connected' event with the session_id.

**Result**: Backend logs:
```
⚠️ WebSocket abc-123... not found, skipping message
Error processing WebSocket message: WebSocket is not connected. Need to call "accept" first.
```

## Fix Required in `frontend/src/components/ContinuousVoiceInterface.tsx`

### Change 1: Import Logger
```typescript
import { logger } from "../utils/logger";
```

### Change 2: Update WebSocket Connection Logic

**CURRENT (BROKEN)**:
```typescript
ws.onopen = () => {
  console.log("✅ WebSocket connected");
  setIsConnected(true);
  setVoiceState("idle");  // ❌ WRONG: Should NOT go to idle, should stay connecting
};
```

**FIXED**:
```typescript
ws.onopen = () => {
  logger.wsConnect(`ws://localhost:8000/ws/voice?user_id=${userId}`);
  // DON'T set isConnected yet - wait for 'connected' event
  // DON'T change voiceState - stay in 'connecting'
};
```

### Change 3: Handle 'connected' Event Properly

**ADD THIS** in `handleWebSocketMessage`:
```typescript
const handleWebSocketMessage = useCallback((message: any) => {
  logger.wsMessageReceived(message.event, message.data?.session_id);

  switch (message.event) {
    case 'connected':
      // ✅ THIS IS THE CRITICAL FIX
      sessionIdRef.current = message.data.session_id;
      logger.wsConnected(message.data.session_id);
      setIsConnected(true);
      setVoiceState("listening");
      // NOW safe to start recording
      startRecording();
      break;
      
    case 'transcription':
      const transcription = message.data.text;
      setCurrentTranscription(transcription);
      onTranscription?.(transcription);
      logger.transcriptionReceived(transcription);
      break;
      
    // ... rest of cases
  }
}, [onTranscription, onResponse, onError, startRecording]);
```

### Change 4: Gate All WebSocket Sends

**UPDATE sendAudioToBackend**:
```typescript
const sendAudioToBackend = useCallback(async () => {
  // ✅ CRITICAL: Check session_id first
  if (!sessionIdRef.current) {
    logger.warn('audio', 'Cannot send: session not established yet');
    return;
  }

  if (audioChunksRef.current.length === 0) {
    return;
  }

  logger.vadSendTriggered();
  
  const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
  audioChunksRef.current = [];
  
  const reader = new FileReader();
  reader.readAsDataURL(audioBlob);
  reader.onloadend = () => {
    const base64Audio = (reader.result as string).split(',')[1];
    
    if (wsRef.current?.readyState === WebSocket.OPEN && sessionIdRef.current) {
      wsRef.current.send(JSON.stringify({
        event: "audio_chunk",
        data: {
          session_id: sessionIdRef.current,
          audio_chunk: base64Audio,
          format: "webm",
          sample_rate: 48000
        }
      }));
      logger.audioChunkSent(audioBlob.size, sessionIdRef.current);
    }
  };
}, []);
```

**UPDATE sendInterruptSignal**:
```typescript
const sendInterruptSignal = useCallback(() => {
  // ✅ CRITICAL: Check session_id first
  if (!sessionIdRef.current) {
    logger.warn('interrupt', 'Cannot send: session not established yet');
    return;
  }

  if (wsRef.current?.readyState === WebSocket.OPEN) {
    wsRef.current.send(JSON.stringify({
      event: "interrupt",
      data: {
        session_id: sessionIdRef.current,
        reason: "user_started_speaking"
      }
    }));
    logger.interruptSent("user_started_speaking");
  }
}, []);
```

### Change 5: Update startVoiceInteraction

**CURRENT (BROKEN)**:
```typescript
const startVoiceInteraction = useCallback(async () => {
  if (!isConnected) {
    connectWebSocket();
    // ❌ WRONG: This timeout is unreliable
    setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        setVoiceState("listening");
        startRecording();
      }
    }, 1000);
  } else {
    setVoiceState("listening");
    startRecording();
  }
}, [isConnected, connectWebSocket, startRecording]);
```

**FIXED**:
```typescript
const startVoiceInteraction = useCallback(async () => {
  if (!isConnected || !sessionIdRef.current) {
    // Connect and wait for 'connected' event
    // (handleWebSocketMessage will call startRecording when ready)
    connectWebSocket();
  } else {
    // Already connected, just start listening
    setVoiceState("listening");
    startRecording();
  }
}, [isConnected, connectWebSocket, startRecording]);
```

### Change 6: Add Logging Throughout

Add logger calls to:
- `startRecording()` → `logger.audioRecordingStart()`
- `stopRecording()` → `logger.audioRecordingStop()`
- `checkVoiceActivity()` when speech detected → `logger.vadSpeechDetected()`
- `checkVoiceActivity()` when silence detected → `logger.vadSilenceDetected(duration)`
- `stopAudioPlayback()` → `logger.playbackStop()`
- `playNextAudioChunk()` start → `logger.playbackStart()`
- When interrupting → `logger.playbackInterrupted()`

## Fix TTS Chunk Size in Backend

### File: `backend/app/core/streaming_handler.py`

```python
async def stream_tts_audio(
    self,
    text: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    chunk_size: int = 12288  # ✅ CHANGED: 4096 → 12288 for ~3Hz
) -> AsyncGenerator[bytes, None]:
```

**Calculation**:
- Typical TTS bitrate: ~32 kbps (4 KB/s)
- At 4096 bytes: ~1 chunk per second → too slow
- At 8192 bytes: ~2 chunks per second → better
- At 12288 bytes: ~3 chunks per second → target ✅

## Testing Sequence

1. **Start Backend**:
   ```bash
   make stop-servers
   make run-server
   tail -f logs/detailed/voice_agent_*.log
   ```

2. **Start Frontend**:
   ```bash
   make run-frontend
   ```

3. **Open Browser**:
   - Navigate to `http://localhost:3000`
   - Open DevTools Console
   - Open Network tab → filter "WS"

4. **Click Microphone**:
   - Should see:
     ```
     Frontend Console:
     🔌 WS | Connecting to ws://localhost:8000/ws/voice?user_id=...
     📥 WS_RECV | event=connected | session=abc12345...
     🔌 WS | Connected | session=abc12345...
     🎤 AUDIO | Recording started with VAD
     ```
   
   - Backend Log:
     ```
     🔌 WS_CONNECT | session=abc12345... | user=def67890...
     📤 WS_SEND | session=abc12345... | event=connected
     ```

5. **Speak a Sentence**:
   - Wait 1 second after stopping
   - Should see:
     ```
     Frontend:
     📊 VAD | Speech detected
     📊 VAD | Silence detected | duration=1000ms
     ℹ️ VAD | Silence threshold reached → sending audio
     📤 WS_SEND | event=audio_chunk | session=abc12345...
     🎤 AUDIO | 📤 SEND | size=153600 bytes
     
     Backend:
     📥 WS_RECV | session=abc12345... | event=audio_chunk
     🎤 AUDIO_RECV | session=abc12345... | size=153600 bytes
     📝 TRANSCRIPTION | session=abc12345... | text='What's the stock price...'
     📤 WS_SEND | session=abc12345... | event=transcription
     🤖 LLM_RESPONSE | session=abc12345... | text='The current price...'
     📤 WS_SEND | session=abc12345... | event=agent_response
     🔊 AUDIO_SEND | session=abc12345... | chunk=0
     📤 WS_SEND | session=abc12345... | event=tts_chunk
     (repeat ~3 times per second)
     ```

6. **Interrupt While Speaking**:
   - Start speaking while agent is talking
   - Should see:
     ```
     Frontend:
     📊 VAD | Speech detected
     🛑 PLAYBACK | 🛑 Playback interrupted by user speech
     📤 WS_SEND | event=interrupt | session=abc12345...
     
     Backend:
     📥 WS_RECV | session=abc12345... | event=interrupt
     🛑 INTERRUPT | session=abc12345... | reason=user_started_speaking
     📤 WS_SEND | session=abc12345... | event=streaming_interrupted
     ```

## Expected Behavior After Fix

1. ✅ **No more "WebSocket not found" errors**
2. ✅ **No more "Need to call accept first" errors**
3. ✅ **Clean connection flow**:
   - Frontend connects
   - Backend sends 'connected'
   - Frontend receives and starts recording
   - User speaks → sends with valid session_id
4. ✅ **Proper logging** in both frontend and backend
5. ✅ **TTS at ~3Hz** (3 chunks per second)
6. ✅ **Error throttling** prevents flooding

## Summary

The key fix is simple but critical:

**❌ WRONG**: Start recording on `ws.onopen`
**✅ CORRECT**: Start recording on `message.event === 'connected'`

This ensures `sessionIdRef.current` is set before any messages are sent, preventing all the current errors.

