# Real-Time Voice Streaming Architecture Design

## Overview

This document outlines the architecture for real-time voice communication between frontend and backend, enabling continuous conversation with instant interruption capabilities.

## How Other Voice Apps Handle Real-Time Communication

### Discord, Zoom, Google Meet, WhatsApp Voice:
1. **Continuous Audio Streaming**: Frontend continuously sends audio chunks (50-100ms) to backend
2. **Server-Side Voice Activity Detection (VAD)**: Backend detects when user starts/stops speaking
3. **Instant Interrupt Detection**: Backend immediately stops TTS when new voice input is detected
4. **Bidirectional Streaming**: Both audio input and output stream simultaneously
5. **Low Latency**: <100ms for interruption detection, <200ms total round-trip

### Key Differences from Current Implementation:
- **Current**: Frontend uses browser Speech Recognition API (client-side ASR)
- **Proposed**: Backend handles all voice processing (server-side ASR + VAD)
- **Current**: Manual interrupt signals
- **Proposed**: Automatic interrupt detection based on voice activity

## Architecture Design

### Frontend Responsibilities
```javascript
// Continuous audio streaming to backend
const mediaRecorder = new MediaRecorder(stream, {
  mimeType: 'audio/webm;codecs=opus',
  audioBitsPerSecond: 16000
});

// Send audio chunks every 100ms
mediaRecorder.ondataavailable = (event) => {
  if (event.data.size > 0) {
    websocket.send(JSON.stringify({
      event: 'audio_chunk',
      data: {
        audio_chunk: base64.encode(event.data),
        session_id: sessionId,
        timestamp: Date.now()
      }
    }));
  }
};

// Handle any response from backend (interrupt current audio)
websocket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  // Any new message = interrupt current audio
  if (isPlayingAudio) {
    stopCurrentAudio();
  }
  
  switch (message.event) {
    case 'tts_chunk':
      playAudioChunk(message.data.audio_chunk);
      break;
    case 'transcription':
      updateTranscript(message.data.text);
      break;
  }
};
```

### Backend Responsibilities

#### 1. Voice Activity Detection (VAD)
```python
class VoiceActivityDetector:
    def __init__(self):
        self.silence_threshold = 0.01
        self.speech_threshold = 0.05
        self.min_speech_duration = 0.3  # seconds
        self.min_silence_duration = 0.5  # seconds
        
    async def detect_voice_activity(self, audio_chunk: bytes) -> bool:
        """Detect if audio chunk contains speech"""
        # Convert audio to numpy array
        audio_data = self.decode_audio(audio_chunk)
        
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_data**2))
        
        # Simple VAD logic
        if rms > self.speech_threshold:
            return True
        return False
```

#### 2. Continuous Audio Processing
```python
class ContinuousVoiceProcessor:
    def __init__(self):
        self.vad = VoiceActivityDetector()
        self.asr = SpeechRecognitionService()
        self.tts = TextToSpeechService()
        self.agent = AgentWrapper()
        
        # State tracking
        self.is_user_speaking = False
        self.is_agent_speaking = False
        self.audio_buffer = []
        self.silence_counter = 0
        
    async def process_audio_chunk(self, session_id: str, audio_chunk: bytes):
        """Process incoming audio chunk"""
        
        # Detect voice activity
        has_speech = await self.vad.detect_voice_activity(audio_chunk)
        
        if has_speech:
            # User started speaking
            if not self.is_user_speaking:
                await self.handle_user_start_speaking(session_id)
            
            # Add to buffer for ASR
            self.audio_buffer.append(audio_chunk)
            self.silence_counter = 0
            
        else:
            # Silence detected
            self.silence_counter += 1
            
            # If user was speaking and silence threshold reached
            if self.is_user_speaking and self.silence_counter > SILENCE_THRESHOLD:
                await self.handle_user_stop_speaking(session_id)
    
    async def handle_user_start_speaking(self, session_id: str):
        """User started speaking - interrupt agent if needed"""
        self.is_user_speaking = True
        
        if self.is_agent_speaking:
            # Interrupt agent immediately
            await self.interrupt_agent(session_id)
            
            # Send interrupt signal to frontend
            await self.send_message(session_id, {
                "event": "user_interrupt",
                "data": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            })
    
    async def handle_user_stop_speaking(self, session_id: str):
        """User stopped speaking - process accumulated audio"""
        self.is_user_speaking = False
        
        if self.audio_buffer:
            # Transcribe accumulated audio
            transcription = await self.asr.transcribe(self.audio_buffer)
            
            if transcription.strip():
                # Send transcription to frontend
                await self.send_message(session_id, {
                    "event": "transcription",
                    "data": {
                        "text": transcription,
                        "confidence": 0.95,
                        "session_id": session_id
                    }
                })
                
                # Process with agent
                await self.process_command(session_id, transcription)
            
            # Clear buffer
            self.audio_buffer = []
    
    async def interrupt_agent(self, session_id: str):
        """Interrupt current agent response"""
        self.is_agent_speaking = False
        
        # Stop any ongoing TTS
        if hasattr(self, 'current_tts_task'):
            self.current_tts_task.cancel()
        
        # Send interrupt signal
        await self.send_message(session_id, {
            "event": "agent_interrupted",
            "data": {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        })
```

#### 3. WebSocket Event Flow
```python
# WebSocket endpoint
@router.websocket("/ws/voice")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    processor = ContinuousVoiceProcessor()
    
    try:
        while True:
            # Receive audio chunk
            data = await websocket.receive_json()
            
            if data["event"] == "audio_chunk":
                audio_chunk = base64.b64decode(data["data"]["audio_chunk"])
                await processor.process_audio_chunk(session_id, audio_chunk)
                
    except WebSocketDisconnect:
        await processor.cleanup(session_id)
```

## Event Flow Diagram

```
Frontend                    Backend
   |                          |
   |-- audio_chunk ---------->|
   |                          |-- VAD detects speech
   |                          |-- interrupt_agent()
   |<-- agent_interrupted ----|
   |                          |
   |-- audio_chunk ---------->|
   |                          |-- VAD detects silence
   |                          |-- ASR transcribe()
   |<-- transcription -------|
   |                          |-- agent.process()
   |                          |-- TTS synthesize()
   |<-- tts_chunk -----------|
   |<-- tts_chunk -----------|
   |<-- tts_complete --------|
```

## Implementation Benefits

### 1. **True Real-Time Communication**
- No manual button pressing
- Continuous listening like human conversation
- Instant interruption detection

### 2. **Better User Experience**
- Natural conversation flow
- No need to wait for agent to finish
- Immediate response to user input

### 3. **Server-Side Control**
- Consistent VAD across all clients
- Better audio processing capabilities
- Centralized voice activity management

### 4. **Scalability**
- Can handle multiple concurrent sessions
- Efficient audio processing pipeline
- Optimized for low-latency communication

## Technical Requirements

### Frontend
- WebRTC MediaRecorder API
- WebSocket connection
- Audio chunk streaming (100ms intervals)
- Automatic audio interruption on new messages

### Backend
- Voice Activity Detection (VAD) library
- Speech Recognition (ASR) service
- Text-to-Speech (TTS) streaming
- WebSocket connection management
- Audio buffer management

### Performance Targets
- **Interrupt Detection**: <100ms
- **Total Round-trip**: <200ms
- **Audio Chunk Size**: 100ms
- **Concurrent Sessions**: 50+

## Migration Strategy

### Phase 1: Backend VAD Implementation
1. Implement server-side Voice Activity Detection
2. Add continuous audio processing pipeline
3. Test with existing WebSocket infrastructure

### Phase 2: Frontend Streaming
1. Replace browser Speech Recognition with continuous streaming
2. Implement automatic audio interruption
3. Update WebSocket event handling

### Phase 3: Optimization
1. Fine-tune VAD parameters
2. Optimize audio chunk sizes
3. Implement connection pooling
4. Add performance monitoring

This architecture provides true real-time voice communication with instant interruption capabilities, matching the behavior of modern voice applications.
