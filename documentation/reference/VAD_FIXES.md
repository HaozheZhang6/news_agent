# Voice Activity Detection (VAD) Fixes

## Issues Found and Fixed

### 1. MediaRecorder Not Producing Data Chunks

**Problem:**
`MediaRecorder.start()` was called without a `timeslice` parameter, causing `ondataavailable` to only fire when recording stops, not continuously. This meant no audio chunks were being accumulated during recording.

**Fix:**
[ContinuousVoiceInterface.tsx:328](frontend/src/components/ContinuousVoiceInterface.tsx#L328)
```typescript
// BEFORE
mediaRecorder.start();

// AFTER
mediaRecorder.start(100); // Request data every 100ms for continuous streaming
```

### 2. Uninitialized Last Speech Time

**Problem:**
`lastSpeechTimeRef.current` was never initialized when recording started. This caused:
- `silenceDuration = Date.now() - 0` = huge number
- Silence detection logic would never trigger properly

**Fix:**
[ContinuousVoiceInterface.tsx:327](frontend/src/components/ContinuousVoiceInterface.tsx#L327)
```typescript
// Initialize to current time when recording starts
lastSpeechTimeRef.current = Date.now();
```

### 3. VAD Threshold Too Sensitive

**Problem:**
`SPEECH_THRESHOLD = 0.01` was too sensitive, detecting background noise as speech. This prevented silence detection from ever triggering.

**Fix:**
[ContinuousVoiceInterface.tsx:64](frontend/src/components/ContinuousVoiceInterface.tsx#L64)
```typescript
// BEFORE
const SPEECH_THRESHOLD = 0.01;

// AFTER
const SPEECH_THRESHOLD = 0.02; // Increased to reduce sensitivity
```

**Note:** This threshold may need further tuning based on testing. Consider making it configurable.

### 4. Added Debug Logging

**Added logging to help diagnose issues:**

1. **Audio level logging** - Shows current audio level vs threshold every 2 seconds
   ```typescript
   console.log(`🎙️ Audio level: ${average.toFixed(4)} (threshold: ${SPEECH_THRESHOLD})`);
   ```

2. **Silence duration logging** - Shows how long user has been silent
   ```typescript
   console.log(`🤐 Silence: ${(silenceDuration / 1000).toFixed(1)}s, chunks: ${audioChunksRef.current.length}`);
   ```

3. **Send trigger logging** - Logs when silence threshold is reached
   ```typescript
   console.log(`📤 Silence threshold reached (${silenceDuration}ms), scheduling send with ${audioChunksRef.current.length} chunks`);
   ```

## How VAD Works

### Recording Flow

1. **Start Recording**
   - User clicks microphone button
   - WebSocket connects to backend
   - MediaRecorder starts capturing audio every 100ms
   - Audio analyzer monitors audio levels

2. **Voice Activity Detection Loop** (runs every 250ms)
   - Analyzes audio waveform to detect speech
   - If audio level > `SPEECH_THRESHOLD` → user is speaking
   - Updates `lastSpeechTimeRef` to current time

3. **Silence Detection**
   - When audio level < `SPEECH_THRESHOLD` → silence detected
   - Calculates `silenceDuration = Date.now() - lastSpeechTimeRef`
   - If `silenceDuration >= SILENCE_THRESHOLD_MS` (1000ms):
     - Schedules audio send after 100ms delay
     - Encodes accumulated audio chunks
     - Sends to backend via WebSocket

4. **Audio Encoding and Sending**
   - Combines all audio chunks into single Blob
   - Encodes as base64 with OPUS codec
   - Sends as WebSocket message with session ID

### VAD Configuration

```typescript
const SILENCE_THRESHOLD_MS = 1000; // 1 second of silence triggers send
const VAD_CHECK_INTERVAL_MS = 250; // Check audio level every 250ms (4Hz)
const SPEECH_THRESHOLD = 0.02; // Audio level threshold to detect speech
```

### Audio Configuration

```typescript
const stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    echoCancellation: true,  // Remove echo
    noiseSuppression: true,  // Reduce background noise
    autoGainControl: true    // Normalize volume
  }
});

const mediaRecorder = new MediaRecorder(stream, {
  mimeType: 'audio/webm;codecs=opus' // Use OPUS codec for compression
});
```

## Testing

### With Frontend Logs

Open browser console and look for:

1. **Recording started:**
   ```
   🎤 Recording started with VAD
   ```

2. **Audio levels being monitored:**
   ```
   🎙️ Audio level: 0.0034 (threshold: 0.02)  ← Silence
   🎙️ Audio level: 0.0456 (threshold: 0.02)  ← Speaking detected
   ```

3. **Silence detection:**
   ```
   🤐 Silence: 1.2s, chunks: 12
   📤 Silence threshold reached (1234ms), scheduling send with 12 chunks
   ```

4. **Audio sent:**
   ```
   📤 WS_SEND | audio_chunk | session=abc123...
   🎵 Compressed with OPUS: 1.0x smaller
   ```

### Expected Behavior

1. **User speaks** → Audio level > 0.02 → VAD detects speech
2. **User stops speaking** → Audio level < 0.02 → Silence detected
3. **1 second passes** → Audio chunks sent to backend
4. **Backend transcribes** → Returns transcription event
5. **Backend processes** → Returns voice_response with TTS
6. **Frontend plays TTS** → User hears response

### If Audio Still Not Sending

Check these in browser console:

1. **Is recording starting?**
   - Look for "🎤 Recording started with VAD"
   - If not, check microphone permissions

2. **Is audio level too low?**
   - Look for "🎙️ Audio level: X.XXXX"
   - If always < 0.02, lower `SPEECH_THRESHOLD` to 0.01

3. **Are chunks being collected?**
   - Look for "🤐 Silence: X.Xs, chunks: N"
   - If chunks = 0, MediaRecorder not producing data

4. **Is silence threshold reached?**
   - Look for "📤 Silence threshold reached"
   - If not appearing after 1s of silence, check timing logic

## Files Modified

1. [frontend/src/components/ContinuousVoiceInterface.tsx](frontend/src/components/ContinuousVoiceInterface.tsx)
   - Line 64: Increased `SPEECH_THRESHOLD` from 0.01 to 0.02
   - Line 285-288: Added audio level logging
   - Line 327: Initialize `lastSpeechTimeRef`
   - Line 328: Added timeslice parameter to `mediaRecorder.start(100)`
   - Line 369-372: Added silence duration logging
   - Line 379: Added send trigger logging

## Recommended Next Steps

1. **Test with real speech:**
   - Open React app in browser
   - Click microphone button
   - Speak for 2-3 seconds
   - Wait 1 second in silence
   - Check console for logs
   - Verify audio sent to backend

2. **Tune threshold if needed:**
   - If too sensitive (detecting noise): increase to 0.03
   - If not sensitive enough (missing speech): decrease to 0.015

3. **Test interruption:**
   - Start agent speaking (send a command)
   - Speak while agent is talking
   - Verify agent stops and listens

4. **Test continuous conversation:**
   - Send multiple queries in a row
   - Verify each is transcribed and answered

## Known Limitations

1. **Background Noise:** VAD may detect consistent background noise as speech. Users should be in quiet environments.

2. **Threshold Tuning:** Optimal threshold varies by:
   - Microphone quality
   - Room acoustics
   - User's speaking volume
   - Background noise level

3. **MediaRecorder Timeslice:** 100ms timeslice means ~10 chunks per second. This is a good balance between:
   - Responsiveness (lower = faster, but more overhead)
   - Performance (higher = more efficient, but less responsive)

## References

- Backend audio handling: [backend/app/core/websocket_manager.py:346](backend/app/core/websocket_manager.py#L346)
- Audio encoder: [frontend/src/utils/audio-encoder.ts](frontend/src/utils/audio-encoder.ts)
- Frontend component: [frontend/src/components/ContinuousVoiceInterface.tsx](frontend/src/components/ContinuousVoiceInterface.tsx)
