# Marmadi - Real-Time Voice Streaming Implementation Plan

## Project Overview
**Marmadi** (meaning "continuous" in Arabic) is the codename for implementing true real-time voice communication in our Voice News Agent, enabling natural conversation flow with instant interruption capabilities.

## Current Problem
- Frontend uses browser Speech Recognition API (client-side)
- Manual interrupt signals required
- No continuous listening capability
- Inconsistent voice activity detection across devices

## Solution: Server-Side Voice Processing

### Core Architecture Changes

#### 1. Frontend → Backend Audio Streaming
```javascript
// Replace browser Speech Recognition with continuous streaming
class ContinuousVoiceStreamer {
  constructor(websocket) {
    this.ws = websocket;
    this.mediaRecorder = null;
    this.isStreaming = false;
  }
  
  async startStreaming() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 16000
    });
    
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.ws.send(JSON.stringify({
          event: 'audio_chunk',
          data: {
            audio_chunk: this.base64Encode(event.data),
            session_id: this.sessionId,
            timestamp: Date.now()
          }
        }));
      }
    };
    
    // Stream every 100ms
    this.mediaRecorder.start(100);
    this.isStreaming = true;
  }
  
  // Any new message from backend = interrupt current audio
  handleBackendMessage(message) {
    if (this.isPlayingAudio) {
      this.stopCurrentAudio();
    }
    
    // Process new message (TTS, transcription, etc.)
    this.processMessage(message);
  }
}
```

#### 2. Backend Voice Activity Detection
```python
class MarmadiVoiceProcessor:
    def __init__(self):
        self.vad = VoiceActivityDetector()
        self.asr = SpeechRecognitionService()
        self.tts = TextToSpeechService()
        self.agent = AgentWrapper()
        
        # State management
        self.session_states = {}  # session_id -> state
        
    async def process_audio_chunk(self, session_id: str, audio_chunk: bytes):
        """Main processing pipeline for audio chunks"""
        
        # Get or create session state
        state = self.session_states.get(session_id, {
            'is_user_speaking': False,
            'is_agent_speaking': False,
            'audio_buffer': [],
            'silence_counter': 0,
            'last_speech_time': None
        })
        
        # Voice Activity Detection
        has_speech = await self.vad.detect_voice_activity(audio_chunk)
        
        if has_speech:
            await self.handle_speech_detected(session_id, audio_chunk, state)
        else:
            await self.handle_silence_detected(session_id, state)
        
        # Update session state
        self.session_states[session_id] = state
    
    async def handle_speech_detected(self, session_id: str, audio_chunk: bytes, state: dict):
        """User started speaking"""
        if not state['is_user_speaking']:
            # User just started speaking
            state['is_user_speaking'] = True
            state['last_speech_time'] = time.time()
            
            # Interrupt agent if speaking
            if state['is_agent_speaking']:
                await self.interrupt_agent(session_id)
                state['is_agent_speaking'] = False
        
        # Add to audio buffer for ASR
        state['audio_buffer'].append(audio_chunk)
        state['silence_counter'] = 0
    
    async def handle_silence_detected(self, session_id: str, state: dict):
        """Silence detected - check if user finished speaking"""
        if state['is_user_speaking']:
            state['silence_counter'] += 1
            
            # If silence threshold reached, process accumulated audio
            if state['silence_counter'] > SILENCE_THRESHOLD:
                await self.process_accumulated_audio(session_id, state)
    
    async def interrupt_agent(self, session_id: str):
        """Immediately interrupt current agent response"""
        # Cancel any ongoing TTS
        if session_id in self.active_tts_tasks:
            self.active_tts_tasks[session_id].cancel()
        
        # Send interrupt signal to frontend
        await self.send_message(session_id, {
            "event": "agent_interrupted",
            "data": {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "reason": "user_speech_detected"
            }
        })
```

#### 3. WebSocket Event Flow
```python
# Updated WebSocket endpoint
@router.websocket("/ws/voice")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    processor = MarmadiVoiceProcessor()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["event"] == "audio_chunk":
                audio_chunk = base64.b64decode(data["data"]["audio_chunk"])
                await processor.process_audio_chunk(session_id, audio_chunk)
                
            elif data["event"] == "start_session":
                await processor.initialize_session(session_id)
                
            elif data["event"] == "end_session":
                await processor.cleanup_session(session_id)
                
    except WebSocketDisconnect:
        await processor.cleanup_session(session_id)
```

## Implementation Phases

### Phase 1: Backend VAD Infrastructure (Week 1)
- [ ] Implement VoiceActivityDetector class
- [ ] Add continuous audio processing pipeline
- [ ] Create session state management
- [ ] Test VAD accuracy with sample audio

### Phase 2: Frontend Streaming (Week 2)
- [ ] Replace browser Speech Recognition with MediaRecorder
- [ ] Implement continuous audio streaming
- [ ] Add automatic audio interruption logic
- [ ] Update WebSocket event handling

### Phase 3: Integration & Testing (Week 3)
- [ ] Integrate backend VAD with existing agent
- [ ] Test real-time interruption scenarios
- [ ] Optimize audio chunk sizes and timing
- [ ] Performance testing with multiple sessions

### Phase 4: Optimization (Week 4)
- [ ] Fine-tune VAD parameters
- [ ] Implement connection pooling
- [ ] Add performance monitoring
- [ ] Deploy and monitor production metrics

## Technical Specifications

### Audio Processing
- **Chunk Size**: 100ms
- **Sample Rate**: 16kHz
- **Format**: WebM with Opus codec
- **Bitrate**: 16kbps

### Performance Targets
- **VAD Latency**: <50ms
- **Interrupt Detection**: <100ms
- **Total Round-trip**: <200ms
- **Concurrent Sessions**: 50+

### Dependencies
```python
# Backend
webrtcvad>=2.0.10          # Voice Activity Detection
librosa>=0.10.0            # Audio processing
numpy>=1.21.0             # Numerical operations
asyncio                    # Async processing

# Frontend
MediaRecorder API          # Audio streaming
WebSocket API              # Real-time communication
```

## Success Metrics

### User Experience
- [ ] Natural conversation flow without button pressing
- [ ] Instant interruption when user starts speaking
- [ ] Consistent behavior across all devices
- [ ] <200ms response time for interruptions

### Technical Performance
- [ ] 99%+ VAD accuracy
- [ ] <100ms interrupt detection
- [ ] Support for 50+ concurrent sessions
- [ ] <1% audio drop rate

### Business Impact
- [ ] Increased user engagement
- [ ] Reduced conversation friction
- [ ] Better user retention
- [ ] Competitive parity with other voice apps

## Risk Mitigation

### Technical Risks
- **VAD Accuracy**: Implement fallback to manual detection
- **Latency Issues**: Optimize audio processing pipeline
- **Memory Leaks**: Implement proper session cleanup
- **Browser Compatibility**: Test across major browsers

### Performance Risks
- **High CPU Usage**: Implement audio processing optimization
- **Network Bandwidth**: Compress audio chunks efficiently
- **Concurrent Sessions**: Implement connection pooling
- **Memory Usage**: Monitor and optimize buffer management

## Future Enhancements

### Advanced Features
- **Echo Cancellation**: Remove agent audio from user input
- **Noise Reduction**: Filter background noise
- **Speaker Identification**: Recognize different users
- **Emotion Detection**: Analyze user sentiment

### Integration Opportunities
- **Multi-language Support**: Detect and switch languages
- **Voice Cloning**: Personalized agent voices
- **Real-time Translation**: Multi-language conversations
- **Voice Commands**: Hands-free navigation

This implementation will transform our voice agent into a truly conversational AI that can engage in natural, real-time dialogue with users.
