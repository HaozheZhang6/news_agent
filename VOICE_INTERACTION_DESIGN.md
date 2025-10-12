# Voice Interaction Design: VAD & Real-time Interruption

## Overview
This document describes the Voice Activity Detection (VAD) and real-time interruption system implemented in the frontend, mirroring the `src.main` architecture.

## Architecture Comparison

### Backend (src.main) ✅
- **VAD Detection**: Uses `voice_activity_detector` to check audio levels
- **Silence Threshold**: `NO_SPEECH_THRESHOLD = 1.0` second
- **Processing**: After 1 second of silence, processes audio with SenseVoice ASR
- **Interruption**: Listener can interrupt speaker thread immediately

### Frontend (ContinuousVoiceInterface) ✅
- **VAD Detection**: Uses Web Audio API `AnalyserNode` to check audio levels
- **Silence Threshold**: `SILENCE_THRESHOLD_MS = 1000` milliseconds (1 second)
- **Processing**: After 1 second of silence, sends audio to backend via WebSocket
- **Interruption**: Stops TTS audio playback when user starts speaking

## Key Features

### 1. Voice Activity Detection (VAD)
```typescript
const checkVoiceActivity = (audioData: Float32Array): boolean => {
  let sum = 0;
  for (let i = 0; i < audioData.length; i++) {
    sum += Math.abs(audioData[i]);
  }
  const average = sum / audioData.length;
  
  // Return true if audio level exceeds threshold (user is speaking)
  return average > SPEECH_THRESHOLD;
};
```

**Configuration:**
- `SPEECH_THRESHOLD = 0.01` - Audio level threshold to detect speech
- `VAD_CHECK_INTERVAL_MS = 100` - Check audio level every 100ms
- `SILENCE_THRESHOLD_MS = 1000` - Send audio after 1 second of silence

### 2. Automatic Audio Sending
When user **stops talking**:
1. VAD detects silence (audio level below threshold)
2. Silence timer starts
3. After 1 second of continuous silence:
   - Stop recording current segment
   - Send audio to backend via WebSocket
   - Backend processes with SenseVoice ASR
   - Backend sends back transcription + LLM response + TTS audio

### 3. Real-time Interruption
When user **starts talking** while agent is speaking:
1. VAD detects voice activity (audio level above threshold)
2. **Immediately** stop TTS audio playback
3. Send interrupt signal to backend
4. Backend stops TTS streaming
5. User's new audio will be processed

```typescript
if (isSpeaking) {
  // User is speaking
  lastSpeechTimeRef.current = Date.now();
  
  // If agent was speaking, interrupt immediately
  if (isPlayingAudioRef.current) {
    console.log("🚨 User started speaking, interrupting agent");
    stopAudioPlayback();
    sendInterruptSignal();
  }
  
  // Clear any pending silence timer
  if (silenceTimerRef.current) {
    clearTimeout(silenceTimerRef.current);
    silenceTimerRef.current = null;
  }
}
```

## WebSocket Communication

### Frontend → Backend

#### 1. Connection
```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/voice?user_id=${userId}`);
```

#### 2. Audio Chunk (after 1 sec silence)
```json
{
  "event": "audio_chunk",
  "data": {
    "session_id": "uuid",
    "audio_chunk": "base64_encoded_audio",
    "format": "webm",
    "sample_rate": 48000
  }
}
```

#### 3. Interrupt Signal
```json
{
  "event": "interrupt",
  "data": {
    "session_id": "uuid",
    "reason": "user_started_speaking"
  }
}
```

### Backend → Frontend

#### 1. Connected
```json
{
  "event": "connected",
  "data": {
    "session_id": "uuid",
    "message": "Connected to Voice News Agent",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### 2. Transcription
```json
{
  "event": "transcription",
  "data": {
    "text": "What's the stock price of AAPL today?",
    "session_id": "uuid"
  }
}
```

#### 3. Agent Response
```json
{
  "event": "agent_response",
  "data": {
    "text": "The current price of Apple stock is...",
    "session_id": "uuid"
  }
}
```

#### 4. TTS Audio Chunks
```json
{
  "event": "tts_chunk",
  "data": {
    "audio_chunk": "base64_encoded_mp3",
    "chunk_index": 0,
    "format": "mp3",
    "session_id": "uuid"
  }
}
```

#### 5. Streaming Complete
```json
{
  "event": "streaming_complete",
  "data": {
    "total_chunks_sent": 42,
    "session_id": "uuid"
  }
}
```

#### 6. Streaming Interrupted
```json
{
  "event": "streaming_interrupted",
  "data": {
    "total_chunks_sent": 15,
    "session_id": "uuid"
  }
}
```

## User Experience Flow

### Scenario 1: Normal Conversation
1. 👤 User clicks microphone button
2. 🎤 Frontend starts recording with VAD
3. 👤 User speaks: "What's the latest news?"
4. ⏱️ User stops speaking
5. ⏱️ Frontend detects 1 second of silence
6. 📤 Frontend sends audio to backend
7. 🔄 Backend processes with ASR → LLM → TTS
8. 📥 Frontend receives transcription + response + audio
9. 🔊 Frontend plays TTS audio
10. 🔁 Goes back to listening

### Scenario 2: User Interrupts Agent
1. 🔊 Agent is speaking (playing TTS audio)
2. 👤 User starts speaking
3. 🚨 VAD detects voice activity immediately
4. 🛑 Frontend stops TTS audio playback
5. 📤 Frontend sends interrupt signal to backend
6. 🛑 Backend stops TTS streaming
7. 👤 User continues speaking
8. ⏱️ User stops speaking
9. ⏱️ Frontend detects 1 second of silence
10. 📤 Frontend sends new audio to backend
11. 🔄 Process continues...

## Configuration

### Frontend (`ContinuousVoiceInterface.tsx`)
```typescript
// VAD Configuration (matching src.main)
const SILENCE_THRESHOLD_MS = 1000;      // 1 second (same as src.main NO_SPEECH_THRESHOLD)
const VAD_CHECK_INTERVAL_MS = 100;      // Check every 100ms
const SPEECH_THRESHOLD = 0.01;          // Audio level threshold

// Audio Configuration
mimeType: 'audio/webm;codecs=opus'      // WebM with Opus codec
sample_rate: 48000                       // MediaRecorder default
```

### Backend (`src/config.py`)
```python
NO_SPEECH_THRESHOLD = 1.0  # Seconds of silence to trigger processing
AUDIO_RATE = 16000         # Sample rate for SenseVoice
AUDIO_CHANNELS = 1         # Mono audio
CHUNK = 1024               # Audio chunk size
```

## Technical Implementation

### Web Audio API Components
1. **MediaRecorder**: Captures audio from microphone
2. **AudioContext**: Creates audio processing pipeline
3. **AnalyserNode**: Analyzes audio frequency/time data for VAD
4. **MediaStreamSource**: Connects microphone to analyser
5. **AudioBufferSourceNode**: Plays TTS audio chunks

### Audio Processing Pipeline
```
Microphone → MediaRecorder → Blob → Base64 → WebSocket → Backend
Backend → Edge-TTS → MP3 chunks → Base64 → WebSocket → Frontend
Frontend → Base64 → ArrayBuffer → AudioBuffer → Speaker
```

### State Management
- `voiceState`: "idle" | "listening" | "speaking" | "connecting"
- `isConnected`: WebSocket connection status
- `isRecordingRef`: Currently recording audio
- `isPlayingAudioRef`: Currently playing TTS audio
- `lastSpeechTimeRef`: Timestamp of last detected speech
- `silenceTimerRef`: Timer for silence detection
- `vadCheckIntervalRef`: Interval for VAD checks

## Benefits

### ✅ Natural Conversation Flow
- User doesn't need to press buttons to send/stop
- Automatically detects when user finishes speaking
- Natural 1-second pause feels comfortable

### ✅ Real-time Interruption
- User can interrupt agent at any time
- No lag - audio stops immediately
- Agent stops speaking when interrupted

### ✅ Continuous Listening
- Always ready to hear user input
- No need to re-activate microphone
- Seamless back-and-forth conversation

### ✅ Low Latency
- VAD checks every 100ms
- Immediate detection of speech/silence
- Fast audio transmission via WebSocket

## Testing

### Test Scenarios

#### 1. Basic Voice Command
- Speak: "What's the stock price of AAPL?"
- Wait 1 second
- Verify audio sent automatically
- Verify transcription received
- Verify agent response audio plays

#### 2. Agent Interruption
- Agent starts speaking
- User interrupts by speaking
- Verify agent audio stops immediately
- Verify user's new command is processed

#### 3. Multiple Turns
- Have a back-and-forth conversation
- Verify each turn processes correctly
- Verify no audio overlap

#### 4. Edge Cases
- Very short speech (< 1 second)
- Long speech (> 10 seconds)
- Background noise
- Multiple rapid interruptions

## Troubleshooting

### Issue: Audio not sending
- Check: Is VAD detecting silence? (Look for console logs)
- Check: Is microphone permission granted?
- Check: Is WebSocket connected?

### Issue: Agent not stopping when interrupted
- Check: Is VAD detecting voice activity?
- Check: Is `isPlayingAudioRef.current` true?
- Check: Is interrupt signal being sent?

### Issue: Audio playing choppy
- Check: Audio chunk queue size
- Check: Network latency
- Check: Browser audio context state

## Future Enhancements

1. **Adaptive Silence Threshold**: Adjust based on user speech patterns
2. **Noise Cancellation**: Better VAD in noisy environments
3. **Multi-language Support**: Language-specific VAD parameters
4. **Visual Feedback**: Show audio waveform while speaking
5. **Offline Mode**: Local ASR/TTS for offline use

## References

- Source: `src/voice_listener_process.py` - Backend VAD implementation
- Source: `src/config.py` - Configuration constants
- Source: `frontend/src/components/ContinuousVoiceInterface.tsx` - Frontend implementation
- Web Audio API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- MediaRecorder API: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder

