# Voice Input Testing Guide

## Overview
The Voice News Agent backend supports real-time voice input via WebSocket. This guide shows you how to test it manually using various tools.

---

## WebSocket Connection

### Endpoint
```
ws://localhost:8000/ws/voice?user_id=YOUR_USER_ID
```

### Connection Flow
1. **Connect** → Receive `connected` event with `session_id`
2. **Send voice messages** → Receive `transcription` and `voice_response`
3. **Disconnect** → Session ends

---

## Message Format

All WebSocket messages are JSON with this structure:
```json
{
  "event": "event_name",
  "data": {
    "session_id": "uuid-from-connected-event",
    ...other fields
  }
}
```

---

## Supported Events

### 1. **voice_command** (Text-based voice input)
Send a transcribed voice command (e.g., from iOS ASR):

```json
{
  "event": "voice_command",
  "data": {
    "session_id": "your-session-id",
    "command": "latest tech news",
    "confidence": 0.95
  }
}
```

**Response:**
- `transcription` event (confirmation)
- `voice_response` event (agent's reply with text and optional audio URL)

---

### 2. **voice_data** (Raw audio input)
Send raw audio chunks for server-side transcription:

```json
{
  "event": "voice_data",
  "data": {
    "session_id": "your-session-id",
    "audio_chunk": "BASE64_ENCODED_AUDIO_DATA",
    "format": "wav",
    "sample_rate": 16000
  }
}
```

**Response:**
- `audio_received` event (acknowledgment)

**Notes:**
- Audio should be base64-encoded
- Supported formats: WAV, PCM
- Recommended sample rate: 16000 Hz, mono

---

### 3. **interrupt** (Stop agent speech)
Interrupt the agent while it's speaking:

```json
{
  "event": "interrupt",
  "data": {
    "session_id": "your-session-id",
    "reason": "user_interruption"
  }
}
```

**Response:**
- `voice_interrupted` event (confirmation)

---

### 4. **start_listening** / **stop_listening**
Control server-side listening state:

```json
{
  "event": "start_listening",
  "data": {
    "session_id": "your-session-id"
  }
}
```

**Response:**
- `listening_started` or `listening_stopped` event

---

## Testing Methods

### Option 1: Browser Test Page (Easiest)

1. Open `test_websocket.html` in your browser
2. Click "Connect"
3. Use the buttons to test:
   - **Send Voice Command**: Simulates text-based voice input
   - **Send Audio Data**: Simulates raw audio chunk
   - **Send Interrupt**: Simulates interruption
4. Watch the message log for responses

---

### Option 2: Postman WebSocket

1. **Create New Request** → Select "WebSocket"
2. **URL**: `ws://localhost:8000/ws/voice?user_id=test_user_123`
3. **Connect**
4. **Receive** the `connected` event → copy the `session_id`
5. **Send** messages:

**Example 1: Voice Command**
```json
{
  "event": "voice_command",
  "data": {
    "session_id": "PASTE_SESSION_ID_HERE",
    "command": "what's the latest on nvidia stock?",
    "confidence": 0.92
  }
}
```

**Example 2: Audio Data**
```json
{
  "event": "voice_data",
  "data": {
    "session_id": "PASTE_SESSION_ID_HERE",
    "audio_chunk": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
    "format": "wav",
    "sample_rate": 16000
  }
}
```

---

### Option 3: Python Script

```python
import asyncio
import websockets
import json

async def test_voice_input():
    uri = "ws://localhost:8000/ws/voice?user_id=python_test"
    
    async with websockets.connect(uri) as websocket:
        # Receive connection event
        response = await websocket.recv()
        data = json.loads(response)
        session_id = data['data']['session_id']
        print(f"Connected! Session: {session_id}")
        
        # Send voice command
        command = {
            "event": "voice_command",
            "data": {
                "session_id": session_id,
                "command": "latest crypto news",
                "confidence": 0.95
            }
        }
        await websocket.send(json.dumps(command))
        print("Sent: latest crypto news")
        
        # Receive responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\nReceived: {data['event']}")
            print(f"Data: {json.dumps(data['data'], indent=2)}")
            
            if data['event'] == 'voice_response':
                break

asyncio.run(test_voice_input())
```

**Run it:**
```bash
pip install websockets
python test_voice.py
```

---

### Option 4: curl + websocat (CLI)

Install websocat:
```bash
brew install websocat  # macOS
# or download from https://github.com/vi/websocat
```

**Connect and test:**
```bash
# Terminal 1: Connect
websocat "ws://localhost:8000/ws/voice?user_id=cli_test"

# You'll receive: {"event":"connected","data":{"session_id":"..."}}
# Copy the session_id

# Then type (replace SESSION_ID):
{"event":"voice_command","data":{"session_id":"SESSION_ID","command":"latest tech news"}}
```

---

## iOS Integration Guide

For your future iOS app with ASR:

### 1. **Use AVAudioEngine + Speech Framework for ASR**
```swift
import Speech
import AVFoundation

// Transcribe locally on iOS
let recognizer = SFSpeechRecognizer()
recognizer.recognitionTask(with: request) { result, error in
    if let result = result {
        let transcribedText = result.bestTranscription.formattedString
        // Send to backend via WebSocket
        sendVoiceCommand(transcribedText)
    }
}
```

### 2. **Send transcription via WebSocket**
```swift
import Starscream  // or use URLSessionWebSocketTask

let socket = WebSocket(url: URL(string: "ws://your-render-url/ws/voice?user_id=ios_user")!)

socket.onEvent = { event in
    switch event {
    case .text(let string):
        let data = string.data(using: .utf8)!
        let json = try! JSONDecoder().decode(WSMessage.self, from: data)
        
        if json.event == "connected" {
            self.sessionId = json.data.sessionId
        } else if json.event == "voice_response" {
            // Play TTS audio or display text
            handleResponse(json.data)
        }
    }
}

func sendVoiceCommand(_ text: String) {
    let message = [
        "event": "voice_command",
        "data": [
            "session_id": sessionId,
            "command": text,
            "confidence": 0.95
        ]
    ]
    let jsonData = try! JSONSerialization.data(withJSONObject: message)
    socket.write(string: String(data: jsonData, encoding: .utf8)!)
}
```

### 3. **Alternative: Send raw audio**
```swift
// Send raw audio chunks for server-side ASR
func sendAudioChunk(_ audioData: Data) {
    let base64Audio = audioData.base64EncodedString()
    let message = [
        "event": "voice_data",
        "data": [
            "session_id": sessionId,
            "audio_chunk": base64Audio,
            "format": "wav",
            "sample_rate": 16000
        ]
    ]
    socket.write(string: try! JSONSerialization.string(message))
}
```

---

## Expected Responses

### 1. Connection Success
```json
{
  "event": "connected",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Connected to Voice News Agent",
    "timestamp": "2025-10-09T12:00:00Z"
  }
}
```

### 2. Transcription Confirmation
```json
{
  "event": "transcription",
  "data": {
    "text": "latest tech news",
    "confidence": 0.95,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "processing_time_ms": 150
  }
}
```

### 3. Voice Response
```json
{
  "event": "voice_response",
  "data": {
    "text": "Here are the latest tech news headlines...",
    "audio_url": "https://your-storage/audio/response_123.mp3",
    "response_type": "news_summary",
    "processing_time_ms": 850,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "news_items": [
      {
        "id": "article-1",
        "title": "AI Breakthrough...",
        "summary": "..."
      }
    ],
    "timestamp": "2025-10-09T12:00:05Z"
  }
}
```

### 4. Error Response
```json
{
  "event": "error",
  "data": {
    "error_type": "command_processing_failed",
    "message": "Failed to fetch news",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## Quick Test Commands

Try these voice commands:
- `"latest tech news"`
- `"what's happening with nvidia stock?"`
- `"give me crypto updates"`
- `"tell me about Tesla"`
- `"any breaking news?"`
- `"deep dive on Apple's latest announcement"`

---

## Troubleshooting

### Connection fails
- Ensure backend is running: `curl http://localhost:8000/health`
- Check WebSocket URL format
- Verify user_id parameter is provided

### No response after sending command
- Check you're using the correct `session_id` from the `connected` event
- Verify JSON format is correct
- Check backend logs for errors

### Audio data not processed
- Ensure audio is base64-encoded
- Verify format is supported (wav, pcm)
- Check sample_rate matches backend expectations (16000 Hz)

---

## Next Steps

1. ✅ Test with browser `test_websocket.html`
2. ✅ Test with Postman WebSocket
3. 🔜 Integrate with iOS app (Speech Framework)
4. 🔜 Add real-time audio streaming
5. 🔜 Deploy to Render and test with production URL

---

## Files
- `test_websocket.html` - Interactive browser test page
- `backend/app/main.py` - WebSocket endpoint handler
- `backend/app/core/websocket_manager.py` - WebSocket message processing

**Server running at:** http://localhost:8000  
**WebSocket endpoint:** ws://localhost:8000/ws/voice

