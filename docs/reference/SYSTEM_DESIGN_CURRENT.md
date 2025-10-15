# Voice News Agent - Current System Design

**Last Updated:** 2025-10-13
**Status:** Working implementation with WAV audio format

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Frontend Design](#frontend-design)
3. [Backend Design](#backend-design)
4. [Communication Protocol](#communication-protocol)
5. [Audio Pipeline](#audio-pipeline)
6. [Data Flow](#data-flow)
7. [Recent Changes](#recent-changes)
8. [Known Issues](#known-issues)
9. [Performance Considerations](#performance-considerations)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  React Frontend (Vite + TypeScript)                     │    │
│  │  ┌─────────────────────┐  ┌──────────────────────┐    │    │
│  │  │ Voice Interface     │  │  Audio Components    │    │    │
│  │  │ - VAD Detection     │  │  - PCM Capture       │    │    │
│  │  │ - State Management  │  │  - WAV Encoding      │    │    │
│  │  │ - WebSocket Client  │  │  - Audio Playback    │    │    │
│  │  └─────────────────────┘  └──────────────────────┘    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket (ws://)
                            │ JSON Messages
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  WebSocket Manager                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ Connection   │  │ Message      │  │ Session     │  │    │
│  │  │ Handler      │  │ Router       │  │ Manager     │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Streaming Handler                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ WAV → PCM    │  │ SenseVoice   │  │ TTS         │  │    │
│  │  │ Conversion   │  │ ASR Model    │  │ Streaming   │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Voice Agent                                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ LangChain    │  │ Tool         │  │ Response    │  │    │
│  │  │ Agent        │  │ Execution    │  │ Generator   │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ API Calls
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Supabase    │  │  News APIs   │  │  Stock APIs  │         │
│  │  Database    │  │  (NewsAPI)   │  │  (YFinance)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend Design

### Component Architecture

```
App.tsx
├── DashboardPage
│   └── ContinuousVoiceInterface ← Main voice component
│       ├── WebSocket Connection Management
│       ├── PCMAudioRecorder (WAV encoding)
│       ├── Voice Activity Detection (VAD)
│       ├── Audio Playback (TTS)
│       └── State Management
└── Other Pages (Profile, Login, etc.)
```

### Key Components

#### 1. ContinuousVoiceInterface.tsx

**Responsibilities:**
- Manage voice interaction lifecycle
- Handle WebSocket communication
- Coordinate audio capture and playback
- Implement Voice Activity Detection (VAD)
- Manage conversation state

**State Machine:**
```
idle → connecting → listening → speaking → listening
  ↑                                          │
  └──────────────────────────────────────────┘
```

**State Transitions:**
- `idle → connecting`: User clicks microphone
- `connecting → listening`: WebSocket connected
- `listening → speaking`: Agent starts speaking
- `speaking → listening`: Agent finishes or user interrupts

#### 2. PCMAudioRecorder (wav-encoder.ts)

**Responsibilities:**
- Capture raw PCM audio from microphone
- Accumulate audio samples in memory
- Encode to WAV format on demand
- Support continuous recording with resets

**Technical Details:**
- Uses ScriptProcessorNode for PCM capture
- Sample rate: 16kHz (matches backend)
- Format: Mono, 16-bit PCM
- Buffer size: 4096 samples per callback

**API:**
```typescript
class PCMAudioRecorder {
  async start(stream: MediaStream): Promise<void>
  stop(): ArrayBuffer | null  // Returns WAV data
  getDuration(): number
  isActive(): boolean
}
```

#### 3. Voice Activity Detection (VAD)

**Algorithm:**
```typescript
// Calculate average audio level
let sum = 0;
for (let i = 0; i < audioData.length; i++) {
  sum += Math.abs(audioData[i]);
}
const average = sum / audioData.length;

// Detect speech
const isSpeaking = average > SPEECH_THRESHOLD; // 0.02
```

**Parameters:**
- `SPEECH_THRESHOLD`: 0.02 (audio level to detect speech)
- `SILENCE_THRESHOLD_MS`: 1000ms (silence duration before send)
- `VAD_CHECK_INTERVAL`: 250ms (check frequency)

**Behavior:**
- Continuously monitors audio levels
- Updates `lastSpeechTimeRef` when speech detected
- Sends audio after 1 second of silence
- Interrupts agent playback when user speaks

### Audio Pipeline - Frontend

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Audio Flow                       │
└─────────────────────────────────────────────────────────────┘

1. User Speech
   ↓
2. MediaStream (getUserMedia)
   ↓
3. ScriptProcessorNode
   ↓ onaudioprocess callback
4. Float32Array PCM samples
   ↓ accumulated in memory
5. VAD Analysis (parallel)
   ├─ AnalyserNode → getFloatTimeDomainData()
   ├─ Calculate average level
   └─ Detect speech/silence
   ↓
6. Silence Detected (1 second)
   ↓
7. Stop PCM Recorder
   ↓ returns WAV data
8. WAV Encoder
   ├─ Create 44-byte WAV header
   ├─ Convert Float32 → Int16 PCM
   └─ Combine into ArrayBuffer
   ↓
9. Base64 Encoding
   ↓
10. WebSocket Send
    {
      event: "audio_chunk",
      data: {
        audio_chunk: "base64...",
        format: "wav",
        sample_rate: 16000,
        session_id: "..."
      }
    }
    ↓
11. Recreate PCM Recorder
    (ready for next utterance)
```

### WebSocket Client

**Connection:**
```typescript
ws://localhost:8000/ws/voice?user_id={userId}
```

**Message Format:**
```typescript
// Outgoing (Frontend → Backend)
interface OutgoingMessage {
  event: "audio_chunk" | "interrupt";
  data: {
    audio_chunk?: string;  // base64
    format?: string;       // "wav"
    is_final?: boolean;
    session_id: string;
    user_id: string;
    sample_rate?: number;
  };
}

// Incoming (Backend → Frontend)
interface IncomingMessage {
  event: "connected" | "transcription" | "voice_response" | "tts_chunk" | "streaming_complete" | "error";
  data: {
    session_id?: string;
    text?: string;
    audio_chunk?: string;  // base64 MP3
    chunk_index?: number;
    is_final?: boolean;
    message?: string;
  };
}
```

---

## Backend Design

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  API Layer (main.py)                                         │
│  - WebSocket endpoint (/ws/voice)                           │
│  - REST endpoints (health, conversation APIs)               │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│  WebSocket Manager (websocket_manager.py)                   │
│  - Connection lifecycle management                          │
│  - Message routing                                          │
│  - Session management                                       │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│  Streaming Handler (streaming_handler.py)                   │
│  - Audio format conversion                                  │
│  - ASR (SenseVoice transcription)                          │
│  - TTS streaming                                            │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│  Voice Agent (agent.py)                                      │
│  - LangChain agent execution                                │
│  - Tool selection and calling                               │
│  - Response generation                                      │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│  External Services                                           │
│  - Supabase (database, sessions)                           │
│  - News APIs (NewsAPI, news aggregation)                   │
│  - Stock APIs (yfinance)                                    │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. WebSocket Manager

**File:** `backend/app/core/websocket_manager.py`

**Responsibilities:**
- Accept WebSocket connections
- Manage active sessions
- Route messages to handlers
- Send responses to clients
- Handle disconnections

**Key Methods:**
```python
async def connect(websocket: WebSocket, user_id: str) -> str
async def disconnect(session_id: str)
async def process_message(websocket: WebSocket, message: str)
async def send_message(session_id: str, message: dict)
```

**Session Management:**
```python
self.active_connections: Dict[str, WebSocket]
self.session_data: Dict[str, dict]
self.user_sessions: Dict[str, str]
```

#### 2. Streaming Handler

**File:** `backend/app/core/streaming_handler.py`

**Responsibilities:**
- Convert audio formats (WAV → PCM if needed)
- Transcribe audio with SenseVoice
- Stream TTS audio chunks
- Buffer and process audio data

**Key Methods:**
```python
async def transcribe_audio(audio_data: bytes, format: str, sample_rate: int) -> str
async def stream_tts_response(session_id: str, text: str)
async def _convert_to_wav(audio_data: bytes, format: str, sample_rate: int) -> bytes
```

**Audio Processing:**
1. Receive base64 audio chunk
2. Decode to bytes
3. Convert to WAV if needed (currently WAV input, no conversion)
4. Save to temporary file
5. Pass to SenseVoice model
6. Return transcription text

#### 3. Voice Agent

**File:** `backend/app/agent.py`

**Responsibilities:**
- Process voice commands
- Execute appropriate tools
- Generate natural language responses
- Handle multi-turn conversations

**Tools Available:**
- `get_stock_price`: Get current stock price
- `get_news`: Fetch latest news
- `add_to_watchlist`: Add stock to user watchlist
- `get_watchlist`: Retrieve user watchlist
- `search_news`: Search news by query

**Processing Flow:**
```python
async def process_voice_command(command: str, user_id: str, session_id: str):
    1. Analyze command intent
    2. Select appropriate tool(s)
    3. Execute tool calls
    4. Generate response
    5. Return response text
```

### Audio Pipeline - Backend

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend Audio Flow                        │
└─────────────────────────────────────────────────────────────┘

1. WebSocket Receive
   ↓ JSON message
2. Parse Message
   ↓ extract audio_chunk (base64)
3. Base64 Decode
   ↓ → bytes
4. Audio Format Check
   ├─ If WAV: use directly ✓
   └─ If WebM/Opus: convert with FFmpeg
   ↓
5. Save to Temp File
   ↓ /tmp/tmpXXXXXX.wav
6. SenseVoice Transcription
   ├─ model.generate(input=file_path)
   ├─ Language detection: auto
   └─ Extract text from result
   ↓
7. Transcription Text
   ↓ send to frontend
8. Voice Agent Processing
   ├─ Analyze intent
   ├─ Execute tools
   └─ Generate response
   ↓
9. Response Text
   ↓ send to frontend
10. TTS Generation
    ├─ Text → Speech synthesis
    ├─ Split into chunks (~100KB each)
    └─ Stream chunks
    ↓
11. TTS Chunks (base64 MP3)
    ↓ send to frontend
12. Streaming Complete
    ↓ signal end
```

---

## Communication Protocol

### WebSocket Handshake

```
Client → Server: ws://localhost:8000/ws/voice?user_id=xxx
Server → Client: HTTP 101 Switching Protocols
Server → Client: {
  "event": "connected",
  "data": {
    "session_id": "uuid-xxx",
    "message": "Connected to Voice News Agent"
  }
}
```

### Message Sequence

```
Frontend                          Backend
   │                                 │
   ├──── audio_chunk ───────────────→│
   │                                 │ (transcribe)
   │←──── transcription ─────────────┤
   │                                 │ (process command)
   │←──── voice_response ────────────┤
   │                                 │ (generate TTS)
   │←──── tts_chunk (1/N) ───────────┤
   │←──── tts_chunk (2/N) ───────────┤
   │←──── ...                         │
   │←──── tts_chunk (N/N) ───────────┤
   │←──── streaming_complete ────────┤
   │                                 │
   ├──── interrupt ─────────────────→│ (user speaks during TTS)
   │←──── streaming_interrupted ─────┤
   │                                 │
```

### Error Handling

```python
# Backend sends error
{
  "event": "error",
  "data": {
    "error_type": "transcription_failed" | "processing_failed" | "invalid_session",
    "message": "Error description",
    "session_id": "uuid-xxx"
  }
}

# Frontend displays error toast
onError?.("Error message")
```

---

## Data Flow

### Complete Voice Interaction Flow

```
1. User clicks microphone button
   ↓
2. Frontend connects WebSocket
   ├─ URL: ws://localhost:8000/ws/voice?user_id=xxx
   └─ State: idle → connecting
   ↓
3. Backend accepts connection
   ├─ Create session_id
   ├─ Store in active_connections
   └─ Send "connected" message
   ↓
4. Frontend receives "connected"
   ├─ Store session_id
   ├─ Start PCM recording
   └─ State: connecting → listening
   ↓
5. User speaks
   ├─ PCM samples accumulated
   └─ VAD monitors audio level
   ↓
6. User stops speaking (1 second silence)
   ├─ VAD triggers send
   ├─ Stop PCM recorder → get WAV data
   ├─ Encode to base64
   ├─ Send audio_chunk message
   └─ Recreate recorder for next utterance
   ↓
7. Backend receives audio_chunk
   ├─ Decode base64 → bytes
   ├─ Save to temp WAV file
   ├─ Transcribe with SenseVoice
   ├─ Send "transcription" message
   ├─ Process with Voice Agent
   ├─ Generate response text
   └─ Send "voice_response" message
   ↓
8. Frontend receives transcription
   ├─ Display in UI
   └─ Call onTranscription callback
   ↓
9. Frontend receives voice_response
   ├─ Display in UI
   ├─ Call onResponse callback
   └─ State: listening → speaking
   ↓
10. Backend generates TTS
    ├─ Text → Speech synthesis
    ├─ Split into chunks
    └─ Stream "tts_chunk" messages
    ↓
11. Frontend receives tts_chunks
    ├─ Decode base64 → ArrayBuffer
    ├─ Add to audio queue
    └─ Play sequentially
    ↓
12. Backend sends "streaming_complete"
    └─ All TTS chunks sent
    ↓
13. Frontend receives "streaming_complete"
    ├─ State: speaking → listening
    └─ Ready for next interaction
    ↓
14. (Optional) User interrupts during TTS
    ├─ VAD detects user speech
    ├─ Stop audio playback
    ├─ Send "interrupt" message
    └─ Backend stops TTS streaming
```

---

## Recent Changes

### Major Updates (2025-10-13)

#### 1. WebSocket Connection Fixes ✅

**Problem:** WebSocket was connecting but immediately disconnecting.

**Root Cause:** React useEffect cleanup function running on every render due to changing dependencies.

**Fix:**
```typescript
// BEFORE (buggy)
useEffect(() => {
  return () => {
    wsRef.current.close();
  };
}, [stopRecording, stopAudioPlayback]); // Dependencies change on every render

// AFTER (fixed)
useEffect(() => {
  return () => {
    if (pcmRecorderRef.current) {
      pcmRecorderRef.current.stop();
    }
    // ... other cleanup
  };
}, []); // Empty array = cleanup only on unmount
```

**Files Changed:**
- `frontend/src/components/ContinuousVoiceInterface.tsx:509-532`

#### 2. VAD Implementation ✅

**Changes:**
- Increased `SPEECH_THRESHOLD` from 0.01 to 0.02 (less sensitive)
- Initialize `lastSpeechTimeRef` when recording starts
- Added MediaRecorder timeslice: `mediaRecorder.start(100)`
- Reset `lastSpeechTimeRef` after sending to prevent multiple sends

**Files Changed:**
- `frontend/src/components/ContinuousVoiceInterface.tsx:64,327,373`

#### 3. Audio Format Migration: WebM → WAV ✅

**Problem:** FFmpeg could not convert WebM chunks from MediaRecorder.

**Root Cause:** Individual WebM chunks from `MediaRecorder.start(100)` are not valid standalone files.

**Solution:** Capture raw PCM audio and encode to WAV format in browser.

**Implementation:**
1. Created `PCMAudioRecorder` class using ScriptProcessorNode
2. Captures raw Float32Array PCM samples
3. Encodes to WAV format (44-byte header + 16-bit PCM)
4. Replaced MediaRecorder with PCM recorder

**Benefits:**
- ✅ WAV files always valid (simple header + PCM)
- ✅ No backend conversion needed
- ✅ SenseVoice works directly with WAV
- ✅ 100% reliability

**Trade-off:**
- ❌ Larger file sizes (3x: ~64KB vs ~20KB for 2 seconds)
- ✅ But guaranteed to work!

**Files Changed:**
- NEW: `frontend/src/utils/wav-encoder.ts` (PCMAudioRecorder, WAVEncoder)
- `frontend/src/utils/audio-encoder.ts:232-251` (encodeWAV method)
- `frontend/src/components/ContinuousVoiceInterface.tsx:53-58,313-331,417-457`

#### 4. Default Question Removal ✅

**Problem:** Backend was using fallback transcription "What's the stock price of AAPL today?" when transcription failed.

**Fix:** Removed all hardcoded fallback questions, now raises proper errors.

**Files Changed:**
- `backend/app/core/streaming_handler.py:142-145,177-181`

#### 5. Anonymous User UUID Fix ✅

**Problem:** Database errors when user_id was "anonymous" (invalid UUID).

**Fix:** Changed default to valid UUID: `00000000-0000-0000-0000-000000000000`

**Files Changed:**
- `backend/app/main.py:186-188`

#### 6. FFmpeg Improvements 🔧

**Added:**
- Debug logging for temp files
- Better error messages
- File existence checks
- Proper error propagation

**Files Changed:**
- `backend/app/core/streaming_handler.py:203-266`

---

## Known Issues

### Current Problems

#### 1. Audio Player Behavior ⚠️

**Issue 1:** Audio player doesn't stop when VAD detects user speaking
- **Current:** Audio continues playing
- **Expected:** Should stop immediately when user starts speaking

**Issue 2:** New incoming audio doesn't play immediately
- **Current:** May wait for queue
- **Expected:** Should play as soon as first chunk received

#### 2. Conversation Latency ⚠️

**Issue:** Conversation feels laggy
- Round-trip time too high
- Need smarter packaging strategy
- Consider streaming optimizations

#### 3. Audio Interruption ⚠️

**Issue:** Interrupt signal sent but backend may not stop TTS immediately
- Current implementation sends interrupt message
- Backend needs to cancel ongoing TTS generation

### Minor Issues

- VAD threshold may need tuning per user/environment
- PCM recorder uses deprecated ScriptProcessorNode (should migrate to AudioWorklet)
- No audio compression (WAV is uncompressed)

---

## Performance Considerations

### Latency Breakdown

```
Total Round-Trip Time: ~3-5 seconds

1. User speaks (2-3s typical utterance)
2. Silence detection (1s)
3. Audio encoding (10-50ms)
4. Network send (10-50ms)
5. Backend transcription (200-500ms)
6. Agent processing (500-2000ms)
   ├─ Intent analysis
   ├─ Tool execution (API calls)
   └─ Response generation
7. TTS generation (500-1000ms)
8. Network receive (10-50ms per chunk)
9. Audio playback starts (immediate)
```

### Optimization Opportunities

#### 1. Reduce Silence Threshold
```typescript
// Current: Wait 1 second after user stops
const SILENCE_THRESHOLD_MS = 1000;

// Optimization: Reduce to 500-700ms
const SILENCE_THRESHOLD_MS = 700; // More responsive
```

#### 2. Stream Audio During Speech
```typescript
// Current: Wait for silence, then send
if (silenceDuration >= SILENCE_THRESHOLD_MS) {
  sendAudioToBackend();
}

// Optimization: Send chunks during speech
if (duration > 2.0 && isSpeaking) {
  sendPartialAudio(); // Stream while speaking
}
```

#### 3. Optimize Agent Processing
```python
# Current: Sequential tool calls
result1 = await tool1()
result2 = await tool2()

# Optimization: Parallel tool execution
results = await asyncio.gather(tool1(), tool2())
```

#### 4. TTS Streaming Optimization
```python
# Current: Wait for full response, then generate TTS
response = await agent.process()
tts_chunks = await generate_tts(response)

# Optimization: Stream TTS as agent generates
async for chunk in agent.stream_response():
    await stream_tts_chunk(chunk)  # Generate and send incrementally
```

### Memory Usage

**Frontend:**
- PCM samples in memory: ~32KB per second (Float32Array)
- WAV encoded: ~32KB per second (16-bit PCM)
- Audio playback queue: ~100-500KB (TTS chunks)

**Backend:**
- Temp WAV files: ~32KB per second (cleaned up after processing)
- SenseVoice model: ~200MB (loaded once)
- Session data: ~1KB per active session

### Network Bandwidth

**Upstream (Frontend → Backend):**
- WAV audio: ~32KB per second
- 3-second utterance: ~96KB
- With base64 encoding: ~128KB

**Downstream (Backend → Frontend):**
- TTS audio (MP3): ~10KB per second
- 5-second response: ~50KB
- Chunked streaming: ~10KB per chunk

---

## Next Steps

### Immediate Fixes Needed

1. **Fix Audio Player VAD Interrupt**
   - Detect user speech during playback
   - Stop audio immediately
   - Clear audio queue
   - Send interrupt signal

2. **Fix Audio Playback Start**
   - Play first TTS chunk immediately
   - Don't wait for all chunks
   - Queue subsequent chunks

3. **Optimize Conversation Flow**
   - Reduce silence threshold (1000ms → 700ms)
   - Consider streaming audio during speech
   - Optimize agent processing time

### Documentation Updates

1. Update this document with audio player fixes
2. Create latency optimization guide
3. Document audio interruption flow
4. Add performance benchmarks

---

## Appendix

### File Structure

```
News_agent/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── ContinuousVoiceInterface.tsx
│   │   ├── utils/
│   │   │   ├── audio-encoder.ts
│   │   │   ├── wav-encoder.ts
│   │   │   └── logger.ts
│   │   └── ...
│   └── ...
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── core/
│   │   │   ├── websocket_manager.py
│   │   │   └── streaming_handler.py
│   │   └── ...
│   └── ...
├── tests/
│   └── voice_samples/
│       ├── wav/
│       └── voice_samples.json
└── docs/
    ├── SYSTEM_DESIGN_CURRENT.md (this file)
    ├── WAV_IMPLEMENTATION_COMPLETE.md
    ├── WEBM_CONVERSION_ISSUE.md
    ├── WEBSOCKET_FIXES.md
    └── VAD_FIXES.md
```

### Key Configuration

**Frontend:**
- WebSocket URL: `ws://localhost:8000/ws/voice`
- Sample Rate: 16000 Hz
- Audio Format: WAV (mono, 16-bit PCM)
- VAD Threshold: 0.02
- Silence Threshold: 1000ms

**Backend:**
- Port: 8000
- ASR Model: SenseVoice
- TTS: System default
- Session Storage: In-memory + Supabase

### Dependencies

**Frontend:**
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Web Audio API

**Backend:**
- FastAPI
- LangChain
- FunASR (SenseVoice)
- FFmpeg
- Supabase Client
- yfinance, newsapi-python

---

**Document End**
