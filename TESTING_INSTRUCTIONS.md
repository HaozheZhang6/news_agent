# Testing Instructions: Voice Interaction with VAD

## Quick Start

### 1. Start Servers
```bash
# Terminal 1: Start Backend
make run-server

# Terminal 2: Start Frontend
make run-frontend
```

### 2. Access Frontend
Open browser: `http://localhost:3000`

### 3. Test Voice Interaction

#### ✅ Step 1: Start Conversation
1. Click the large **microphone button** in the center
2. Button turns **blue** and starts pulsing (listening mode)
3. Green dot in top-right shows connection status

#### ✅ Step 2: Speak Naturally
1. Say: "What's the stock price of Apple today?"
2. Keep speaking naturally - don't rush
3. **Stop speaking and wait 1 second**
4. Audio automatically sends (you'll see console log: "📤 Sending audio to backend")

#### ✅ Step 3: Receive Response
1. You'll see your transcription appear: "You said: ..."
2. Agent response appears: "Agent: The current price of Apple stock is..."
3. Button turns **green** (agent speaking)
4. You'll hear the agent's voice response

#### ✅ Step 4: Interrupt Agent (Real-time)
1. While agent is speaking, **start talking**
2. Agent audio **stops immediately**
3. Interrupt signal sent to backend (console: "🚨 User started speaking, interrupting agent")
4. Your new audio will be processed after 1 second of silence

#### ✅ Step 5: Continue Conversation
1. After agent finishes, button returns to **blue** (listening)
2. Speak again for next turn
3. Process repeats seamlessly

## Test Scenarios

### Scenario 1: Stock Price Query
**You**: "What's the stock price of Tesla today?"
**Wait**: 1 second of silence
**Expected**: Transcription appears → Agent responds with TSLA price → Audio plays

### Scenario 2: News Query
**You**: "What's the latest news about Apple?"
**Wait**: 1 second of silence
**Expected**: Transcription appears → Agent responds with Apple news → Audio plays

### Scenario 3: Follow-up Question
**You**: "What's the stock price of Microsoft?"
**Wait**: Agent responds with price
**You**: "Tell me more about it" (interrupt while agent is speaking)
**Expected**: Agent stops immediately → New question processed

### Scenario 4: Deep Dive
**You**: "What happened to Tesla stock today?"
**Wait**: Agent starts explaining
**You**: "Could you explain more about the first point?" (interrupt)
**Expected**: Agent stops → Processes new question

## Key Features to Test

### ✅ Voice Activity Detection (VAD)
- **Purpose**: Automatically detect when you stop talking
- **How it works**: Monitors audio level every 100ms
- **Threshold**: If silent for 1 second, sends audio
- **Test**: Speak, then stay silent - audio should send after ~1 second

### ✅ Auto-send After Silence
- **Purpose**: No need to press "stop" button
- **How it works**: 1 second after you stop talking, audio automatically sends
- **Test**: Say something, count to 1, should see "📤 Sending audio to backend"

### ✅ Real-time Interruption
- **Purpose**: Interrupt agent when you want to speak
- **How it works**: VAD detects your voice → stops agent audio immediately
- **Test**: Let agent speak, then start talking - agent should stop instantly

### ✅ Continuous Listening
- **Purpose**: Always ready for your input
- **How it works**: Microphone stays active between turns
- **Test**: After agent finishes, speak again - no need to click button

## Console Logs to Look For

### Frontend Console (`http://localhost:3000`)

#### Good Logs ✅
```
🔌 Connecting to WebSocket...
✅ WebSocket connected
🎯 Session established: abc-123-def-456
🎤 Recording started with VAD
📤 Sending audio to backend (detected silence)
✅ Audio sent to backend
📥 Received: transcription
🎤 Transcribed: "What's the stock price of AAPL today?"
📥 Received: agent_response
🤖 Agent response: "The current price of Apple stock is..."
📥 Received: tts_chunk
✅ TTS streaming complete
```

#### Interruption Logs ✅
```
🚨 User started speaking, interrupting agent
🛑 Interrupt signal sent to backend
```

#### Error Logs ❌
```
❌ WebSocket error: ...
❌ Error starting recording: ...
❌ Error handling TTS chunk: ...
```

### Backend Console (Terminal)

#### Good Logs ✅
```
✅ WebSocket connected: abc-123 for user def-456
🎤 Processing audio chunk for session abc-123
🎤 Transcribed: 'What's the stock price of AAPL today?'
✅ Streamed 42 TTS chunks to abc-123
```

#### Interruption Logs ✅
```
🛑 TTS streaming interrupted for abc-123
⚠️ Interrupt signal sent for session abc-123
```

#### Error Logs ❌
```
❌ Error handling audio chunk: ...
⚠️ WebSocket abc-123 not found
Error processing WebSocket message: ...
```

## Troubleshooting

### Issue: "Microphone access denied"
**Solution**: Grant microphone permission in browser settings
- Chrome: Settings → Privacy → Site Settings → Microphone
- Allow access for `localhost:3000`

### Issue: "Audio not sending automatically"
**Possible causes**:
1. Not waiting 1 full second of silence
2. Background noise triggering VAD
3. Microphone sensitivity too high/low

**Debug**:
- Check console for VAD activity logs
- Try speaking in quieter environment
- Adjust `SPEECH_THRESHOLD` if needed (currently 0.01)

### Issue: "Agent not stopping when I interrupt"
**Possible causes**:
1. VAD not detecting your voice
2. Microphone level too low
3. Audio context not initialized

**Debug**:
- Check console: should see "🚨 User started speaking"
- Speak louder or closer to microphone
- Check browser audio permissions

### Issue: "WebSocket connection failed"
**Possible causes**:
1. Backend not running
2. Port 8000 already in use
3. CORS issues

**Debug**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if port 8000 is in use
lsof -i :8000

# Restart backend
make stop-servers
make run-server
```

### Issue: "Audio playing choppy or delayed"
**Possible causes**:
1. Slow network connection
2. Backend processing slow
3. Audio buffer issues

**Debug**:
- Check network latency
- Check backend logs for processing time
- Monitor audio queue size in console

## Advanced Testing

### Test 1: Rapid Interruptions
1. Start agent speaking
2. Interrupt 3 times in quick succession
3. **Expected**: Each interruption handled correctly, no audio overlap

### Test 2: Long Conversation
1. Have 10+ turn conversation
2. **Expected**: No memory leaks, consistent performance

### Test 3: Background Noise
1. Play music or TV in background
2. Try voice commands
3. **Expected**: VAD should still detect your voice (may need louder speech)

### Test 4: Multiple Tabs
1. Open 2-3 browser tabs with frontend
2. Click microphone in each
3. **Expected**: Each tab gets own WebSocket connection, no interference

## Performance Metrics

### Expected Latency
- **VAD Detection**: < 100ms
- **Silence Detection**: ~1000ms (by design)
- **Audio Send**: < 200ms
- **ASR Processing**: 500-1000ms
- **LLM Response**: 1-2 seconds
- **TTS Generation**: 500-1000ms
- **Audio Playback Start**: < 100ms
- **Interruption**: < 100ms (immediate)

### Expected User Experience
- **Total response time**: 3-5 seconds from end of speech to start of audio
- **Interruption latency**: < 100ms (feels instant)
- **Natural conversation flow**: Seamless back-and-forth

## Browser Compatibility

### ✅ Tested & Supported
- Chrome 90+
- Edge 90+
- Safari 14+ (may have audio format limitations)
- Firefox 88+

### ⚠️ Known Issues
- Safari: WebM audio may not work, might need MP3 fallback
- Firefox: Some audio context limitations
- Mobile browsers: May have different audio permissions

## Next Steps After Testing

1. **If everything works**: Ready for production deployment!
2. **If issues found**: Check troubleshooting section above
3. **For customization**: Adjust VAD parameters in `ContinuousVoiceInterface.tsx`:
   - `SILENCE_THRESHOLD_MS`: Adjust delay before sending
   - `SPEECH_THRESHOLD`: Adjust voice detection sensitivity
   - `VAD_CHECK_INTERVAL_MS`: Adjust checking frequency

## Documentation References

- **VAD Design**: See `VOICE_INTERACTION_DESIGN.md`
- **WebSocket Protocol**: See `backend/app/design.md`
- **Backend Implementation**: See `backend/app/core/websocket_manager.py`
- **Frontend Implementation**: See `frontend/src/components/ContinuousVoiceInterface.tsx`
- **Local Voice System**: See `src/voice_listener_process.py`

