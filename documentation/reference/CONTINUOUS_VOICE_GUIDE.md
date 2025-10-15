# 🎤 Continuous Voice Agent Guide

## Overview

This implements the **same continuous streaming architecture** as `src/main.py` but for web browsers:

- **Parallel "Threads"**: Listener (Speech Recognition) and Speaker (Audio Playback) run simultaneously
- **Real-time Interruption**: Say "stop" or "pause" to interrupt the agent anytime
- **Continuous Listening**: Click once to start, speaks automatically when you talk
- **Voice Activity Detection**: Browser's Speech Recognition provides automatic VAD

---

## 🚀 How to Use

### 1. Start Continuous Session

**Click the purple microphone button once** 🎤

```
Status: "Listening continuously..."
Button: Turns red 🔴
Stop button: Appears ⏹
```

### 2. Speak Naturally

**Just speak - no need to press/hold**

- The agent listens continuously
- Your words appear in real-time as you speak
- Final transcription sent when you pause

Example:
```
YOU: "Tell me the latest tech news"
  ↓ (shows in real-time)
  
AGENT: "Here are the latest headlines..."
  ↓ (text + audio streams)
  
(Agent is speaking, but still listening!)
```

### 3. Interrupt Anytime

**While agent is speaking:**

**Option A: Say interrupt command**
```
"Stop"
"Pause"  
"Quiet"
"Silence"
```

**Option B: Click STOP button ⏹**

Result:
- Agent immediately stops speaking
- Audio playback cancelled
- Returns to listening mode

### 4. End Session

**Say:** "Exit", "Quit", or "Goodbye"

**Or:** Click the microphone button again

---

## 🎯 Key Features

### Continuous Listening
- ✅ **Always active** - No need to press button for each question
- ✅ **Auto-restart** - Recognition restarts automatically if it stops
- ✅ **Real-time feedback** - See interim results as you speak

### Real-time Interruption
- ✅ **Instant stop** - Say "stop" to interrupt immediately
- ✅ **Audio cancellation** - Stops TTS playback instantly
- ✅ **Queue clearing** - Removes buffered audio chunks

### Parallel Operation (Simulated)
- ✅ **Listener "Thread"** - Browser Speech Recognition (continuous)
- ✅ **Speaker "Thread"** - Audio playback queue (non-blocking)
- ✅ **Interrupt handling** - Stop commands processed with priority

---

## 🏗️ Architecture Comparison

### Original (`src/main.py`)
```python
# Two Python threads
listener_thread = start_listener_thread(ipc_manager)
speaker_thread = start_speaker_thread(ipc_manager)

# IPC for communication
command_queue = SmartPriorityQueue()
interrupt_event = threading.Event()
```

### Web Version (`voice_continuous.html`)
```javascript
// Two async "threads"
recognition.continuous = true;  // Listener
audioQueue + playback;          // Speaker

// WebSocket for communication
ws.send({ event: 'voice_command' });
ws.send({ event: 'interrupt' });
```

---

## 📊 Event Flow

### Normal Command Flow
```
1. USER speaks → Speech Recognition detects
2. Interim results → Shows in UI (real-time)
3. Final result → Sends to backend via WebSocket
4. Backend processes → Agent generates response
5. Response streams back → Text + TTS audio chunks
6. Audio plays → While still listening for interrupts
```

### Interrupt Flow
```
1. USER says "stop" → Speech Recognition detects
2. Interrupt sent → WebSocket interrupt event
3. Backend stops → Cancels ongoing TTS
4. Frontend stops → Clears audio queue
5. Returns to listening → Ready for next command
```

---

## 🎮 Commands Reference

### Interrupt Commands
- "stop", "halt", "pause"
- "quiet", "silence", "shut up"

### Navigation
- "skip", "next" - Skip current topic
- "go back", "repeat" - Repeat last response
- "tell me more" - Deep dive into topic

### Content Requests
- "latest news", "tech news", "business news"
- "stock price", "AAPL stock"
- "weather forecast"

### Control
- "speak faster", "speak slower"
- "speak louder", "speak quieter"

### Exit
- "exit", "quit", "goodbye"

---

## 🔧 Technical Details

### Browser Speech Recognition
```javascript
recognition = new SpeechRecognition();
recognition.continuous = true;    // Keep listening
recognition.interimResults = true; // Real-time feedback
recognition.lang = 'en-US';

recognition.onresult = (event) => {
    // Process interim and final results
    // Send commands, show feedback
};
```

### WebSocket Events
```javascript
// Client → Server
{ event: 'start_listening', data: {...} }
{ event: 'voice_command', data: { command: "..." } }
{ event: 'interrupt', data: {...} }
{ event: 'stop_listening', data: {...} }

// Server → Client
{ event: 'listening_started', data: {...} }
{ event: 'voice_response', data: { text: "..." } }
{ event: 'tts_chunk', data: { audio_chunk: "..." } }
{ event: 'voice_interrupted', data: {...} }
{ event: 'streaming_complete', data: {...} }
```

### Audio Streaming
```javascript
// Queue-based playback (non-blocking)
audioQueue.push(chunk);
if (!isPlaying) playNextAudio();

// Interrupt stops all queued audio
function stopAllAudio() {
    audioQueue = [];
    audioPlayer.pause();
}
```

---

## 🎯 Usage Examples

### Example 1: News Request
```
[Click mic button - session starts]

YOU: "Tell me the latest tech news"
AGENT: "Here are the latest headlines: 1. Google launches..."
  (Agent speaking, you can still interrupt)
  
YOU: "Stop"
AGENT: [stops immediately]

YOU: "Tell me about AI instead"
AGENT: "Here's what's happening with AI..."
```

### Example 2: Stock Query
```
[Session active]

YOU: "What's the Apple stock price?"
AGENT: "Apple stock is currently at $175..."

YOU: "Add it to my watchlist"
AGENT: "I've added AAPL to your watchlist"
```

### Example 3: Interruption
```
[Session active, agent speaking]

AGENT: "The Federal Reserve announced today that interest rates..."

YOU: "Stop, tell me sports news instead"
AGENT: [stops]
AGENT: "Here are the latest sports headlines..."
```

---

## 🐛 Troubleshooting

### "Speech Recognition not supported"
- **Solution**: Use Google Chrome or Microsoft Edge
- Safari has limited support

### Recognition keeps stopping
- **Check**: Make sure you clicked the mic button to start session
- **Check**: Browser didn't block microphone permission
- **Try**: Refresh page and grant permissions again

### Agent doesn't respond
- **Check**: Backend server is running (`make run-server`)
- **Check**: WebSocket connected (status shows "Connected")
- **Try**: Click "Test: Latest news" button

### Can't interrupt agent
- **Try**: Say "stop" clearly
- **Try**: Click the STOP button ⏹
- **Check**: Make sure session is active (red mic button)

### Audio doesn't play
- **Check**: Browser autoplay policy (click page first)
- **Check**: Volume is not muted
- **Try**: Refresh page

---

## 📝 Comparison: Three Interfaces

| Feature | voice_test.html | voice_realtime.html | voice_continuous.html |
|---------|----------------|---------------------|----------------------|
| **Model** | Click → Record → Click → Send | Hold → Speak → Release | Click once → Continuous |
| **Listening** | Manual start/stop | Hold to record | Always active |
| **Interruption** | Not supported | Not supported | ✅ Real-time |
| **Transcription** | After stop | Real-time while holding | Real-time continuous |
| **Best For** | Simple testing | Quick queries | Full conversations |
| **Like src/main.py** | ❌ No | ⚠️ Partial | ✅ Yes |

---

## 🎉 Summary

**The continuous voice interface (`voice_continuous.html`) provides the same experience as the local `src/main.py`:**

- ✅ Click once to start continuous listening
- ✅ Speak anytime without pressing buttons
- ✅ Interrupt agent in real-time with voice commands
- ✅ Parallel listener and speaker operation
- ✅ Real-time transcription feedback
- ✅ Streaming audio responses

**This is the web equivalent of your multi-threaded local agent!** 🚀

