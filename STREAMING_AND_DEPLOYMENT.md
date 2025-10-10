# Streaming Voice + Render Free Tier Deployment

## ✅ Yes, Both Are Possible!

---

## 1. Streaming Voice Implementation

### Current Status
- ✅ WebSocket connection established
- ✅ Bidirectional communication working
- ✅ Basic voice command processing
- 🔄 **Needs enhancement**: Real-time audio streaming + chunked TTS responses

### Streaming Architecture

```
Client (iOS/Web)          WebSocket          Backend
     |                       |                   |
     |----audio chunk------->|                   |
     |                       |---process ASR---->|
     |                       |<--partial text----|
     |<--transcription-------|                   |
     |                       |                   |
     |                       |---generate TTS--->|
     |<--audio chunk 1-------|<--stream back-----|
     |<--audio chunk 2-------|                   |
     |<--audio chunk 3-------|                   |
     |                       |                   |
```

---

## 2. Enhanced WebSocket for Streaming

### Add Streaming Events

**New events to implement:**

1. **`partial_transcription`** - Send intermediate ASR results
```json
{
  "event": "partial_transcription",
  "data": {
    "session_id": "...",
    "text": "latest tech",
    "is_final": false
  }
}
```

2. **`tts_chunk`** - Stream TTS audio in chunks
```json
{
  "event": "tts_chunk",
  "data": {
    "session_id": "...",
    "audio_chunk": "BASE64_ENCODED_AUDIO",
    "chunk_index": 0,
    "total_chunks": 10,
    "format": "mp3"
  }
}
```

3. **`streaming_complete`** - Signal end of stream
```json
{
  "event": "streaming_complete",
  "data": {
    "session_id": "...",
    "total_chunks_sent": 10,
    "duration_ms": 1500
  }
}
```

### Implementation Plan

**backend/app/core/streaming_handler.py** (new file):
```python
import asyncio
import base64
from typing import AsyncGenerator
import edge_tts

class StreamingVoiceHandler:
    """Handle streaming voice input/output"""
    
    async def stream_tts_audio(
        self, 
        text: str, 
        voice: str = "en-US-AriaNeural"
    ) -> AsyncGenerator[bytes, None]:
        """Stream TTS audio in chunks"""
        communicate = edge_tts.Communicate(text, voice)
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    
    async def process_audio_stream(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
        session_id: str,
        ws_manager
    ):
        """Process incoming audio stream with SenseVoice"""
        buffer = bytearray()
        
        async for chunk in audio_chunks:
            buffer.extend(chunk)
            
            # Process every 1 second of audio (16000 samples)
            if len(buffer) >= 32000:  # 16kHz * 2 bytes * 1 sec
                # Send to ASR (SenseVoice or other)
                partial_text = await self.transcribe_chunk(bytes(buffer))
                
                # Send partial result
                await ws_manager.send_message(session_id, {
                    "event": "partial_transcription",
                    "data": {
                        "text": partial_text,
                        "is_final": False,
                        "session_id": session_id
                    }
                })
                
                buffer.clear()
        
        # Process final chunk
        if buffer:
            final_text = await self.transcribe_chunk(bytes(buffer))
            await ws_manager.send_message(session_id, {
                "event": "partial_transcription",
                "data": {
                    "text": final_text,
                    "is_final": True,
                    "session_id": session_id
                }
            })
    
    async def transcribe_chunk(self, audio_data: bytes) -> str:
        """Transcribe audio chunk (placeholder for SenseVoice)"""
        # TODO: Integrate SenseVoice or Whisper
        return "transcribed text"
```

**Update websocket_manager.py:**
```python
from .streaming_handler import StreamingVoiceHandler

class WebSocketManager:
    def __init__(self):
        # ... existing code ...
        self.streaming_handler = StreamingVoiceHandler()
    
    async def handle_voice_data_streaming(self, session_id: str, data: Dict[str, Any]):
        """Handle streaming audio data"""
        audio_chunk = base64.b64decode(data.get("audio_chunk", ""))
        is_final = data.get("is_final", False)
        
        # Buffer chunks and process
        if session_id not in self.audio_buffers:
            self.audio_buffers[session_id] = bytearray()
        
        self.audio_buffers[session_id].extend(audio_chunk)
        
        # Process if buffer is large enough or final chunk
        if len(self.audio_buffers[session_id]) >= 32000 or is_final:
            # Transcribe
            text = await self.streaming_handler.transcribe_chunk(
                bytes(self.audio_buffers[session_id])
            )
            
            # Send partial transcription
            await self.send_message(session_id, {
                "event": "partial_transcription",
                "data": {
                    "text": text,
                    "is_final": is_final,
                    "session_id": session_id
                }
            })
            
            self.audio_buffers[session_id].clear()
    
    async def stream_tts_response(self, session_id: str, text: str):
        """Stream TTS audio back to client"""
        chunk_index = 0
        total_chunks = 0
        
        async for audio_chunk in self.streaming_handler.stream_tts_audio(text):
            # Send audio chunk
            await self.send_message(session_id, {
                "event": "tts_chunk",
                "data": {
                    "audio_chunk": base64.b64encode(audio_chunk).decode(),
                    "chunk_index": chunk_index,
                    "format": "mp3",
                    "session_id": session_id
                }
            })
            chunk_index += 1
        
        # Send completion
        await self.send_message(session_id, {
            "event": "streaming_complete",
            "data": {
                "total_chunks_sent": chunk_index,
                "session_id": session_id
            }
        })
```

---

## 3. Render Free Tier Considerations

### ✅ What Works on Free Tier

| Feature | Free Tier Support | Notes |
|---------|-------------------|-------|
| WebSocket | ✅ Yes | Full support, persistent connections |
| Streaming | ✅ Yes | Works great over WebSocket |
| Docker | ✅ Yes | Can use Dockerfile |
| 512 MB RAM | ⚠️ Limited | Enough for basic voice, may need optimization |
| Sleeps after 15 min | ⚠️ Yes | Cold start ~30-60s |
| 750 hrs/month | ✅ Yes | ~1 month continuous |

### ⚠️ Limitations to Work Around

**1. Memory (512 MB)**
```python
# Optimize memory usage
- Don't load large ML models (use APIs instead)
- Stream audio instead of buffering entire files
- Clear buffers after processing
- Use edge-tts (lightweight) instead of local TTS models
```

**2. Sleep after 15 min inactivity**
```python
# Solutions:
- Accept cold starts (30-60s first request)
- Use UptimeRobot to ping every 14 min (keeps awake)
- Display "Waking up..." message to users
```

**3. CPU limits**
```python
# Optimize:
- Use external APIs for heavy lifting (OpenAI, ElevenLabs)
- Don't run SenseVoice locally (use OpenAI Whisper API or client-side iOS ASR)
- Cache aggressively with Upstash
```

### Recommended Architecture for Free Tier

```
iOS App (Client-side ASR)
    ↓ (send transcribed text)
WebSocket → Render Backend (512MB RAM)
    ↓ (process with LLM API)
OpenAI/ZhipuAI API (external)
    ↓ (get response)
Edge-TTS (lightweight, no local model)
    ↓ (stream audio chunks)
WebSocket → iOS App
```

**Key optimizations:**
- ✅ ASR on iOS (Speech Framework) → send text only
- ✅ Use LLM APIs (no local models)
- ✅ Use edge-tts (no local TTS model)
- ✅ Stream responses (low memory)
- ✅ Cache with Upstash Redis

---

## 4. Deployment Configuration for Streaming

### Update render.yaml

```yaml
services:
  - type: web
    name: voice-news-agent-api
    env: docker
    plan: free
    dockerContext: backend
    dockerfilePath: Dockerfile
    healthCheckPath: /health
    
    # Streaming-specific settings
    envVars:
      # ... existing vars ...
      
      # WebSocket settings (important for streaming)
      - key: MAX_WEBSOCKET_CONNECTIONS
        value: 10  # Lower for free tier
      
      - key: WEBSOCKET_TIMEOUT
        value: 600  # 10 min max per session
      
      - key: AUDIO_CHUNK_SIZE
        value: 4096  # Smaller chunks for streaming
      
      - key: STREAM_TTS_CHUNKS
        value: true
      
      - key: USE_EXTERNAL_ASR
        value: true  # Don't load SenseVoice locally
```

### Update Dockerfile for Streaming

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install only essential dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Don't install heavy audio processing libs (PyAudio, etc)
COPY requirements.txt .

# Install minimal requirements
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    websockets \
    edge-tts \
    supabase \
    httpx \
    redis \
    python-dotenv

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

# Use single worker for free tier
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}", "--workers", "1"]
```

---

## 5. iOS Client Streaming Example

### SwiftUI + WebSocket Streaming

```swift
import SwiftUI
import Speech
import Starscream

class VoiceStreamingViewModel: ObservableObject {
    @Published var isRecording = false
    @Published var transcription = ""
    @Published var isPlaying = false
    
    private var socket: WebSocket?
    private var sessionId: String?
    private var audioEngine: AVAudioEngine?
    private var audioPlayer: AVAudioPlayer?
    private var audioBuffer = Data()
    
    func connect() {
        let url = URL(string: "wss://your-app.onrender.com/ws/voice?user_id=ios_user")!
        socket = WebSocket(request: URLRequest(url: url))
        
        socket?.onEvent = { [weak self] event in
            switch event {
            case .text(let string):
                self?.handleMessage(string)
            default:
                break
            }
        }
        
        socket?.connect()
    }
    
    func startRecording() {
        // Use iOS Speech Recognition (client-side ASR)
        let recognizer = SFSpeechRecognizer()
        let audioSession = AVAudioSession.sharedInstance()
        try? audioSession.setCategory(.record, mode: .measurement)
        
        audioEngine = AVAudioEngine()
        let inputNode = audioEngine!.inputNode
        
        let recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        
        recognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            if let result = result {
                // Send transcribed text in real-time
                self?.sendVoiceCommand(result.bestTranscription.formattedString)
                self?.transcription = result.bestTranscription.formattedString
            }
        }
        
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }
        
        audioEngine?.prepare()
        try? audioEngine?.start()
        isRecording = true
    }
    
    func stopRecording() {
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        isRecording = false
    }
    
    func sendVoiceCommand(_ text: String) {
        guard let sessionId = sessionId else { return }
        
        let message: [String: Any] = [
            "event": "voice_command",
            "data": [
                "session_id": sessionId,
                "command": text,
                "confidence": 0.95
            ]
        ]
        
        if let jsonData = try? JSONSerialization.data(withJSONObject: message),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            socket?.write(string: jsonString)
        }
    }
    
    func handleMessage(_ message: String) {
        guard let data = message.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let event = json["event"] as? String,
              let eventData = json["data"] as? [String: Any] else { return }
        
        switch event {
        case "connected":
            sessionId = eventData["session_id"] as? String
            
        case "tts_chunk":
            // Receive and play streaming audio chunks
            if let audioChunkBase64 = eventData["audio_chunk"] as? String,
               let audioData = Data(base64Encoded: audioChunkBase64) {
                playAudioChunk(audioData)
            }
            
        case "streaming_complete":
            print("Stream completed")
            isPlaying = false
            
        default:
            break
        }
    }
    
    func playAudioChunk(_ audioData: Data) {
        audioBuffer.append(audioData)
        
        if !isPlaying {
            isPlaying = true
            audioPlayer = try? AVAudioPlayer(data: audioBuffer)
            audioPlayer?.play()
        }
    }
}
```

---

## 6. Testing Streaming Locally

### Step 1: Update backend for streaming (I can implement this)
### Step 2: Test with enhanced test_websocket.html
### Step 3: Deploy to Render
### Step 4: Test with iOS app

---

## 7. Cost Comparison

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/mo | 512MB RAM, sleeps after 15min, 750hrs |
| **Starter** | $7/mo | 512MB RAM, always on, no sleep |
| **Standard** | $25/mo | 2GB RAM, better for streaming |

**Recommendation:** Start with **Free tier** → validate → upgrade to Starter if successful

---

## 8. Alternative: Serverless Streaming

If Render free tier is too limited:

**Vercel Edge Functions + WebSocket**
- Free tier: 100GB-hours
- Better for lightweight streaming
- Use with Supabase Realtime instead of WebSocket

**Cloudflare Workers + Durable Objects**
- Free tier: 100k requests/day
- WebSocket support via Durable Objects
- Global edge network

---

## Decision Matrix

| Use Case | Best Option | Why |
|----------|-------------|-----|
| MVP testing | Render Free | Easy Docker deploy, WebSocket works |
| Low traffic (<100 users) | Render Free + UptimeRobot | Keep-alive pings prevent sleep |
| Medium traffic | Render Starter ($7) | Always-on, no cold starts |
| High traffic/low latency | Vercel + Supabase | Global edge, better performance |

---

## Next Steps

1. ✅ Current: WebSocket working locally
2. 🔄 **Add streaming handlers** (I can implement now)
3. 🔄 **Test streaming locally**
4. 🔄 **Deploy to Render free tier**
5. 🔄 **Test with iOS client**
6. 🔄 **Monitor performance → upgrade if needed**

**Want me to implement the streaming handlers now?** 🚀

