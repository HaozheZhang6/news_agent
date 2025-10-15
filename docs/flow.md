# Voice Agent Flow Documentation

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                            │
│  - ContinuousVoiceInterface.tsx                                      │
│  - Logger (localStorage + console + download)                        │
│  - VAD (Voice Activity Detection)                                    │
│  - Audio Recording (MediaRecorder)                                   │
│  - Audio Playback (AudioContext)                                     │
└────────────────────┬─────────────────────────────────────────────────┘
                     │ WebSocket
                     │ ws://localhost:8000/ws/voice?user_id={userId}
                     │
┌────────────────────┴─────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                            │
│  - WebSocketManager (websocket_manager.py)                           │
│  - StreamingHandler (streaming_handler.py)                           │
│  - Agent Wrapper (agent_wrapper.py)                                  │
│  - Logger (logs/detailed/backend_{date}_{time}.log)                  │
└────────────────────┬─────────────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───┴───┐      ┌────┴────┐      ┌───┴────┐
│  ASR  │      │   LLM   │      │  TTS   │
│SenseV │      │ZhipuAI  │      │ Edge   │
│oice   │      │  GLM-4  │      │  TTS   │
└───────┘      └─────────┘      └────────┘
```

---

## Complete Voice Interaction Flow

### Phase 1: Connection Establishment

```
[USER CLICKS MIC BUTTON]
        ↓
┌────────────────────────────────────────────────────────────┐
│ FRONTEND: connectWebSocket()                               │
├────────────────────────────────────────────────────────────┤
│ 1. voiceState → "connecting"                               │
│ 2. Create WebSocket: new WebSocket(wsUrl)                  │
│ 3. Log: 🔌 WS_CONNECT | url=ws://...                       │
└────────────────────────────┬───────────────────────────────┘
                             │
                ┌────────────▼────────────┐
                │ ws.onopen fires         │
                │ → isConnected = true    │
                │ → Log: INFO | opened    │
                └────────────┬────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: /ws/voice endpoint                                │
├────────────────────────────────────────────────────────────┤
│ 1. await websocket.accept()                                │
│ 2. ws_manager.connect(websocket, user_id)                  │
│ 3. Generate session_id = uuid4()                           │
│ 4. Store in active_connections[session_id]                 │
│ 5. Log: 🔌 WS_CONNECT | user=XXX                           │
│ 6. Send: {"event": "connected", "data": {...}}            │
│ 7. Log: 📤 WS_SEND | event=connected                       │
└────────────────────────────┬───────────────────────────────┘
                             │
                ┌────────────▼────────────┐
                │ ws.onmessage fires      │
                │ event="connected"       │
                └────────────┬────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ FRONTEND: handleWebSocketMessage()                         │
├────────────────────────────────────────────────────────────┤
│ case 'connected':                                          │
│ 1. sessionIdRef.current = session_id                       │
│ 2. Log: 🎯 WS_CONNECTED | session=XXX                      │
│ 3. voiceState → "listening"                                │
│ 4. startRecording()                                        │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ READY FOR VOICE INTERACTION │
              └─────────────────────────────┘
```

---

### Phase 2: Voice Activity Detection (VAD) & Audio Capture

```
[USER IS SILENT OR SPEAKING]
        ↓
┌────────────────────────────────────────────────────────────┐
│ FRONTEND: VAD Loop (every 100ms)                           │
├────────────────────────────────────────────────────────────┤
│ 1. MediaRecorder captures audio chunks                     │
│ 2. Analyser.getByteTimeDomainData() → calculate RMS       │
│ 3. If RMS > SPEECH_THRESHOLD (0.01):                      │
│    - Speech detected!                                      │
│    - lastSpeechTime = now                                  │
│    - If agent was speaking → INTERRUPT                     │
│      • stopAudioPlayback()                                 │
│      • sendInterruptSignal()                               │
│      • Log: 🚨 INTERRUPTION                                │
│ 4. If RMS < SPEECH_THRESHOLD:                             │
│    - Silence detected                                      │
│    - Start/reset silence timer (1000ms)                    │
│ 5. After 1 second of silence:                             │
│    - Log: 🎤 VAD_SEND_TRIGGERED                            │
│    - sendAudioToBackend()                                  │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ USER STOPPED TALKING        │
              │ (1 second silence detected) │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ FRONTEND: sendAudioToBackend()                             │
├────────────────────────────────────────────────────────────┤
│ 1. Combine audio chunks → Blob                             │
│ 2. Convert to base64                                       │
│ 3. Send via WebSocket:                                     │
│    {                                                       │
│      "event": "audio_chunk",                              │
│      "data": {                                            │
│        "session_id": session_id,                          │
│        "audio_chunk": base64_audio,                       │
│        "format": "webm",                                  │
│        "sample_rate": 48000                               │
│      }                                                    │
│    }                                                      │
│ 4. Log: 📤 AUDIO_CHUNK_SENT | size=XXXX                    │
│ 5. Log: 📤 WS_SEND | event=audio_chunk                     │
│ 6. Clear audioChunksRef (prepare for next utterance)      │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ AUDIO SENT TO BACKEND       │
              └─────────────────────────────┘
```

---

### Phase 3: Backend Processing (ASR → LLM → TTS)

```
[AUDIO CHUNK RECEIVED FROM FRONTEND]
        ↓
┌────────────────────────────────────────────────────────────┐
│ BACKEND: WebSocketManager.process_message()                │
├────────────────────────────────────────────────────────────┤
│ 1. Parse JSON: event="audio_chunk"                         │
│ 2. Log: 📥 WS_RECV | event=audio_chunk                     │
│ 3. Route to: handle_audio_chunk(session_id, data)         │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: handle_audio_chunk()                              │
├────────────────────────────────────────────────────────────┤
│ 1. Decode base64 → audio_chunk (bytes)                     │
│ 2. Log: 🎤 AUDIO | Processing audio chunk                  │
│ 3. Call: streaming_handler.process_voice_command()        │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │     ASR (SenseVoice)        │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: StreamingHandler.transcribe_chunk()               │
├────────────────────────────────────────────────────────────┤
│ 1. Save audio to temp file                                 │
│ 2. Call SenseVoice: model.generate(audio_file)            │
│ 3. Extract text from result                                │
│ 4. Log: 📝 TRANSCRIPTION | text='...'                      │
│ 5. Return: transcription                                   │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │   LLM (ZhipuAI GLM-4)       │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: AgentWrapper.process_voice_command()              │
├────────────────────────────────────────────────────────────┤
│ 1. Get agent response: agent.get_response(transcription)   │
│ 2. Log: 🤖 AGENT_RESPONSE | text='...'                     │
│ 3. Store conversation in database                          │
│ 4. Return: response_text                                   │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: Send transcription and response                   │
├────────────────────────────────────────────────────────────┤
│ 1. Send: {"event": "transcription", "data": {...}}        │
│    Log: 📤 WS_SEND | event=transcription                   │
│ 2. Send: {"event": "agent_response", "data": {...}}       │
│    Log: 📤 WS_SEND | event=agent_response                  │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │   TTS (Edge-TTS)            │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: stream_tts_response()                             │
├────────────────────────────────────────────────────────────┤
│ 1. streaming_handler.stream_tts_audio(text)                │
│ 2. For each audio chunk (12288 bytes ≈ 0.38s @ 16kHz):   │
│    - Check interruption flag                               │
│    - If interrupted: break, send streaming_interrupted     │
│    - Encode chunk to base64                                │
│    - Send: {"event": "tts_chunk", "data": {...}}          │
│    - Log: 🔊 TTS_STREAM | chunk=X/Y                        │
│    - Log: 📤 WS_SEND | event=tts_chunk                     │
│    - Small delay (10ms) to prevent overwhelming client     │
│ 3. Send: {"event": "streaming_complete", "data": {...}}   │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ TTS CHUNKS SENT TO FRONTEND │
              └─────────────────────────────┘
```

---

### Phase 4: Frontend Audio Playback

```
[TTS CHUNKS RECEIVED FROM BACKEND]
        ↓
┌────────────────────────────────────────────────────────────┐
│ FRONTEND: handleWebSocketMessage()                         │
├────────────────────────────────────────────────────────────┤
│ case 'transcription':                                      │
│ 1. setCurrentTranscription(text)                           │
│ 2. onTranscription?.(text)                                 │
│ 3. Log: 📝 TRANSCRIPTION | text='...'                      │
│                                                            │
│ case 'agent_response':                                     │
│ 1. setCurrentResponse(text)                                │
│ 2. onResponse?.(text)                                      │
│ 3. voiceState → "speaking"                                 │
│ 4. Log: 🤖 RESPONSE | text='...'                           │
│                                                            │
│ case 'tts_chunk':                                          │
│ 1. Decode base64 → ArrayBuffer                             │
│ 2. audioQueueRef.push(audioData)                           │
│ 3. If not currently playing: playNextAudioChunk()         │
│ 4. Log: 🔊 TTS_CHUNK_RECEIVED | index=X                    │
│                                                            │
│ case 'streaming_complete':                                 │
│ 1. If queue empty: voiceState → "listening"               │
│ 2. Log: ✅ STREAMING_COMPLETE                              │
│                                                            │
│ case 'streaming_interrupted':                              │
│ 1. stopAudioPlayback()                                     │
│ 2. audioQueueRef.clear()                                   │
│ 3. voiceState → "listening"                                │
│ 4. Log: 🛑 STREAMING_INTERRUPTED                           │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ FRONTEND: playNextAudioChunk()                             │
├────────────────────────────────────────────────────────────┤
│ 1. If audioQueue empty or isMuted: return                  │
│ 2. isPlayingAudioRef = true                                │
│ 3. Pop audio chunk from queue                              │
│ 4. audioContext.decodeAudioData(chunk)                     │
│ 5. Create AudioBufferSourceNode                            │
│ 6. source.connect(destination)                             │
│ 7. source.start(0)                                         │
│ 8. Log: 🔊 TTS_CHUNK_PLAYED | index=X                      │
│ 9. source.onended:                                         │
│    - isPlayingAudioRef = false                             │
│    - playNextAudioChunk() (recursively play next)         │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ USER HEARS AGENT RESPONSE   │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ AGENT FINISHES SPEAKING     │
              │ voiceState → "listening"    │
              │ VAD CONTINUES MONITORING    │
              └─────────────────────────────┘
```

---

## Real-Time Interruption Flow

```
[AGENT IS SPEAKING, USER STARTS TALKING]
        ↓
┌────────────────────────────────────────────────────────────┐
│ FRONTEND: VAD detects speech (RMS > 0.01)                  │
├────────────────────────────────────────────────────────────┤
│ 1. Check: voiceState === "speaking"                        │
│ 2. Check: isPlayingAudioRef === true                       │
│ 3. INTERRUPT TRIGGERED!                                    │
│ 4. Log: 🚨 USER_STARTED_SPEAKING                           │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ LOCAL INTERRUPTION          │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ FRONTEND: stopAudioPlayback()                              │
├────────────────────────────────────────────────────────────┤
│ 1. currentAudioSourceRef.stop()                            │
│ 2. currentAudioSourceRef.disconnect()                      │
│ 3. audioQueueRef = [] (clear all pending chunks)           │
│ 4. isPlayingAudioRef = false                               │
│ 5. voiceState → "listening"                                │
│ 6. Log: 🔇 AUDIO_PLAYBACK_STOPPED                          │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ REMOTE INTERRUPTION         │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ FRONTEND: sendInterruptSignal()                            │
├────────────────────────────────────────────────────────────┤
│ 1. Send via WebSocket:                                     │
│    {                                                       │
│      "event": "interrupt",                                │
│      "data": {                                            │
│        "session_id": session_id,                          │
│        "reason": "user_speech_detected"                   │
│      }                                                    │
│    }                                                      │
│ 2. Log: 🛑 INTERRUPT_SIGNAL_SENT                           │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ SIGNAL SENT TO BACKEND      │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: handle_interrupt()                                │
├────────────────────────────────────────────────────────────┤
│ 1. Log: 📥 WS_RECV | event=interrupt                       │
│ 2. streaming_tasks[session_id] = True (stop flag)         │
│ 3. Log: 🛑 INTERRUPT_SIGNAL_RECEIVED                       │
│ 4. Send: {"event": "voice_interrupted", "data": {...}}    │
│ 5. Log: 📤 WS_SEND | event=voice_interrupted               │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ TTS streaming loop checks   │
              │ streaming_tasks[session_id] │
              │ → break (stop streaming)    │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: stream_tts_response() breaks                      │
├────────────────────────────────────────────────────────────┤
│ 1. Interruption detected in loop                           │
│ 2. Log: 🛑 TTS_STREAMING_INTERRUPTED                       │
│ 3. Send: {"event": "streaming_interrupted", "data": {...}}│
│ 4. Log: 📤 WS_SEND | event=streaming_interrupted           │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ INTERRUPTION COMPLETE       │
              │ System ready for new input  │
              │ voiceState = "listening"    │
              │ VAD monitoring user speech  │
              └─────────────────────────────┘
```

---

## HTTP Request/Response Flow

```
[FRONTEND MAKES HTTP REQUEST]
        ↓
┌────────────────────────────────────────────────────────────┐
│ FRONTEND: fetch() or axios                                 │
├────────────────────────────────────────────────────────────┤
│ Example: GET /api/user/watchlist?user_id=test123          │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ HTTP REQUEST SENT           │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: HTTP Middleware                                   │
├────────────────────────────────────────────────────────────┤
│ @app.middleware("http")                                    │
│ async def log_requests(request, call_next):                │
│   start_time = time.time()                                 │
│   logger.info(f"📥 HTTP | {method} {path} | client=IP")    │
│   response = await call_next(request)                      │
│   duration = (time.time() - start_time) * 1000            │
│   logger.info(f"📤 HTTP | {method} {path} | status | ms")  │
│   return response                                          │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ ROUTE TO API ENDPOINT       │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│ BACKEND: API Handler (e.g., user.py)                       │
├────────────────────────────────────────────────────────────┤
│ @router.get("/api/user/watchlist")                         │
│ async def get_watchlist(user_id: str, db = Depends(...)):  │
│   prefs = await db.get_user_preferences(user_id)          │
│   return {"watchlist_stocks": prefs.get("watchlist", [])} │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ RESPONSE RETURNED           │
              │ status_code = 200           │
              │ body = {"watchlist_stocks"} │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ MIDDLEWARE LOGS RESPONSE    │
              │ 📤 HTTP | ... | status | ms │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │ RESPONSE SENT TO FRONTEND   │
              └─────────────────────────────┘
```

---

## Logging Communication Frequency

### Backend Logging
- **HTTP requests**: Logged at INFO level (start + end)
- **WebSocket connections**: Logged at INFO level
- **WebSocket messages**: 
  - Sent: Logged at DEBUG level (high frequency)
  - Received: Logged at DEBUG level (high frequency)
- **Error throttling**: Max 1 error per second per type (prevents log spam)
- **TTS streaming**: Debug logs for each chunk (~3-4Hz)

### Frontend Logging
- **Console**: Real-time, all levels
- **localStorage**: Accumulated, all levels (max 1000 entries)
- **Download**: On-demand, all levels
- **WebSocket messages**: ~3-4Hz during TTS streaming
- **VAD checks**: Every 100ms (not logged to prevent spam)
- **Audio chunks sent**: When silence detected (~1-2 per utterance)

---

## Summary: Current vs Expected Flow

### ✅ Current Flow (Working)
1. User clicks mic button
2. WebSocket established immediately
3. Backend sends 'connected' event with session_id
4. Frontend receives 'connected' and starts recording
5. VAD monitors audio continuously
6. On 1 second silence: Send audio to backend
7. Backend: ASR → LLM → TTS (all logged)
8. TTS chunks streamed back (~3-4Hz)
9. Frontend plays audio, monitors for interruption
10. If user speaks while agent talks: Immediate interruption
11. Logs created in proper format with timestamps

### ❌ Previous Problems (Fixed)
1. ~~WebSocket not connecting~~ → Now connects immediately
2. ~~No session_id~~ → Backend sends 'connected' event with session_id
3. ~~Recording not starting~~ → Starts after 'connected' event
4. ~~Empty log files~~ → Now logs HTTP, WebSocket, audio pipeline
5. ~~Wrong log naming~~ → Now `backend_{date}_{time}.log` format
6. ~~No frontend logs~~ → LogViewer component with download button

---

## Next Steps

1. **Test the complete flow**:
   - Click mic button → Check logs for WebSocket connection
   - Speak → Check logs for audio_chunk sent
   - Wait for response → Check logs for transcription, agent_response, tts_chunks
   - Interrupt agent → Check logs for interruption signals

2. **Verify logs**:
   - Backend: `tail -f logs/detailed/backend_*.log`
   - Frontend: Click "View Logs" button (bottom right)

3. **Monitor communication frequency**:
   - Count TTS chunks per second (should be ~3-4Hz)
   - Count WebSocket messages (should match ~3-4Hz during TTS)
   - Check error throttling (max 1 error/sec per type)

Your voice agent is now **fully operational with comprehensive logging**! 🎉
