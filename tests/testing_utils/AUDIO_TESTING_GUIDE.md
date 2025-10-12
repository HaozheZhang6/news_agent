# Audio Testing Guide for Voice News Agent

## Overview

This guide documents the complete audio testing pipeline for the Voice News Agent, including:
- Text-to-speech voice sample generation
- Audio compression with modern codecs (OPUS)
- Base64 encoding for WebSocket transmission
- End-to-end testing procedures
- Session validation and traceability

## Table of Contents

1. [Audio Pipeline Stages](#audio-pipeline-stages)
2. [Voice Sample Generation](#voice-sample-generation)
3. [Audio Compression](#audio-compression)
4. [Encoding for WebSocket](#encoding-for-websocket)
5. [Testing Tools](#testing-tools)
6. [Traceability and Validation](#traceability-and-validation)

---

## Audio Pipeline Stages

The audio testing pipeline consists of the following stages:

```
Text Query → TTS Generation → WAV File → Compression (OPUS) → Base64 Encoding → WebSocket JSON → Backend Processing
```

### Stage 1: Text Query
- User query as plain text (e.g., "What's the stock price of NVDA today?")
- Stored as reference for validation

### Stage 2: TTS Generation
- Convert text to speech using a TTS engine (e.g., edge-tts, gTTS)
- Generate WAV audio file
- Typically 16kHz, mono, 16-bit PCM

### Stage 3: Compression (OPUS)
- Compress WAV file using modern codecs
- OPUS is preferred for speech (WebRTC standard)
- Achieves 5-8x compression ratio
- Maintains good quality for speech at 64kbps

### Stage 4: Base64 Encoding
- Encode compressed audio to Base64 string
- Package in WebSocket-compatible JSON format
- Include metadata (format, session ID, compression info)

### Stage 5: WebSocket Transmission
- Send JSON message to backend WebSocket endpoint
- Receive transcription, agent response, and TTS audio chunks
- Track conversation flow and session data

### Stage 6: Validation
- Retrieve session data from backend API
- Validate transcription matches original query
- Verify all conversation turns were logged correctly

---

## Voice Sample Generation

### Using Edge-TTS (Recommended)

```bash
# Install edge-tts
pip install edge-tts

# Generate voice sample
edge-tts --text "What's the stock price of NVDA today?" \
  --voice en-US-AriaNeural \
  --write-media tests/voice_samples/test_price_nvda_today.wav
```

### Using Google TTS (Alternative)

```python
from gtts import gTTS

text = "What's the latest news about NVDA?"
tts = gTTS(text=text, lang='en', slow=False)
tts.save("tests/voice_samples/test_news_nvda_latest.wav")
```

### Voice Sample Naming Convention

Format: `test_<type>_<ticker>_<action>_[modifiers].wav`

Examples:
- `test_price_nvda_today.wav` - Price query for NVDA
- `test_news_aapl_latest.wav` - Latest news for AAPL
- `test_analysis_tsla_deeper.wav` - Deep analysis for TSLA
- `test_followup_what_happened.wav` - Follow-up query

---

## Audio Compression

### Using voice_encoder.py

The `voice_encoder.py` utility handles compression and encoding.

#### Compress Single File (OPUS)

```bash
python tests/testing_utils/voice_encoder.py \
  tests/voice_samples/test_price_nvda_today.wav \
  -o tests/voice_samples/encoded_compressed_opus/test_price_nvda_today_compressed_opus.json \
  --codec opus
```

#### Batch Compress Directory

```bash
python tests/testing_utils/voice_encoder.py \
  --batch tests/voice_samples/ \
  --codec opus
```

Output: Creates `encoded_compressed_opus/` directory with all compressed+encoded files.

#### Test Compression Without Saving

```bash
python tests/testing_utils/voice_encoder.py \
  --test tests/voice_samples/test_price_nvda_today.wav \
  --codec opus
```

### Supported Codecs

| Codec | Extension | Bitrate | Best For | Compression Ratio |
|-------|-----------|---------|----------|-------------------|
| **opus** | .opus | 64k | Speech (WebRTC) | 5-8x |
| aac | .m4a | 128k | General audio | 3-4x |
| mp3 | .mp3 | 128k | Wide compatibility | 3-4x |
| webm | .webm | 64k | Web browsers | 5-8x |

**Recommendation:** Use OPUS for production - it's the WebRTC standard and provides best compression for speech.

### Compression Benefits

- **Bandwidth:** 5-8x less data to transmit
- **Latency:** Faster upload times over network
- **Cost:** Reduced data transfer costs
- **Performance:** Backend processes smaller files faster

**Example:**
- Original WAV: 87,630 bytes
- Compressed OPUS: 17,599 bytes
- **Savings:** 79.9% (5.0x compression)

---

## Encoding for WebSocket

### Encoded JSON Format

```json
{
  "event": "audio_chunk",
  "data": {
    "audio_chunk": "BASE64_ENCODED_AUDIO_DATA...",
    "format": "opus",
    "is_final": true,
    "session_id": "uuid-string",
    "user_id": "uuid-string",
    "sample_rate": 16000,
    "file_size": 17599,
    "original_filename": "test_price_nvda_today.wav",
    "encoded_at": "2025-10-12T13:56:00.000000",
    "compression": {
      "codec": "opus",
      "original_size": 87630,
      "compressed_size": 17599,
      "compression_ratio": 5.0,
      "bitrate": "64k",
      "sample_rate": "16000",
      "description": "Opus - Best for real-time speech (WebRTC standard)"
    }
  }
}
```

### Key Fields

- `audio_chunk`: Base64-encoded compressed audio data
- `format`: Audio format (opus, wav, webm, mp3)
- `session_id`: Will be replaced by actual session ID from WebSocket connection
- `compression`: Metadata about compression applied

---

## Testing Tools

### 1. test_websocket_simple.py

Basic WebSocket test with single audio file.

```bash
python test_websocket_simple.py \
  tests/voice_samples/encoded_compressed_opus/test_news_nvda_latest_compressed_opus.json
```

**Output:**
- Connection status
- Transcription received
- Agent response
- TTS chunks count
- Processing time

### 2. test_compressed_audio.py

Detailed compression analysis test.

```bash
python test_compressed_audio.py \
  tests/voice_samples/encoded_compressed_opus/test_price_nvda_today_compressed_opus.json
```

**Output:**
- Detailed compression statistics
- WebSocket connection flow
- Complete response logging
- Performance metrics

### 3. test_comprehensive_opus.py

**NEW:** Multi-query test with session validation.

```bash
python test_comprehensive_opus.py \
  tests/voice_samples/encoded_compressed_opus/test_price_nvda_today_compressed_opus.json \
  tests/voice_samples/encoded_compressed_opus/test_news_nvda_latest_compressed_opus.json
```

**Features:**
- Tests multiple queries in single session
- Retrieves session data from backend API
- Validates conversation turns
- Verifies transcriptions match queries
- Checks TTS chunks were sent
- Comprehensive validation report

**Output:**
```
🧪 WebSocket Audio Pipeline Test
📁 Test File #1: test_price_nvda_today_compressed_opus.json
   🎤 Transcription: What's the stock price of NVDA today?
   🤖 Agent Response: The latest stock price for NVDA is $245.27.
   🔊 TTS chunks received: 9

📁 Test File #2: test_news_nvda_latest_compressed_opus.json
   🎤 Transcription: What's the latest news about NVDA?
   🤖 Agent Response: Here are the latest headlines about NVDA...
   🔊 TTS chunks received: 12

🔍 Validating Session from Backend API
   Session ID: 2ce2ede4-775a-4287-9637-f318d4daa31d
   Total Turns: 2
   Matched Queries: 2
   ✅ Session validation successful!
```

---

## Traceability and Validation

### Backend Conversation Logging

The backend now logs comprehensive conversation details:

**Location:** `logs/conversations/`

**Files:**
- `turns_YYYYMMDD.jsonl` - All conversation turns for the day
- `session_<session_id>.json` - Complete session data
- `model_info.json` - Model loading information

### Session Data Structure

```json
{
  "session_id": "2ce2ede4-775a-4287-9637-f318d4daa31d",
  "user_id": "1e8c6024-...",
  "session_start": "2025-10-12T13:57:02.982Z",
  "session_end": "2025-10-12T13:57:15.441Z",
  "total_turns": 2,
  "total_interruptions": 0,
  "turns": [
    {
      "session_id": "2ce2ede4-...",
      "user_id": "1e8c6024-...",
      "timestamp": "2025-10-12T13:57:07.779Z",
      "transcription": "What's the stock price of NVDA today?",
      "agent_response": "The latest stock price for NVDA is $245.27.",
      "processing_time_ms": 4850.5,
      "audio_format": "opus",
      "audio_size_bytes": 17599,
      "tts_chunks_sent": 9,
      "error": null,
      "metadata": {
        "timestamp": "2025-10-12T13:57:07.779327",
        "confidence": 0.95
      }
    },
    {
      "session_id": "2ce2ede4-...",
      "user_id": "1e8c6024-...",
      "timestamp": "2025-10-12T13:57:12.115Z",
      "transcription": "What's the latest news about NVDA?",
      "agent_response": "Here are the latest headlines about NVDA...",
      "processing_time_ms": 3287.2,
      "audio_format": "opus",
      "audio_size_bytes": 18432,
      "tts_chunks_sent": 12,
      "error": null,
      "metadata": {
        "timestamp": "2025-10-12T13:57:12.115889",
        "confidence": 0.95
      }
    }
  ]
}
```

### API Endpoints for Session Retrieval

#### Get Session Data

```bash
GET /api/conversation-sessions/sessions/{session_id}
```

**Example:**
```bash
curl http://localhost:8000/api/conversation-sessions/sessions/2ce2ede4-775a-4287-9637-f318d4daa31d
```

#### Get Model Information

```bash
GET /api/conversation-sessions/models/info
```

**Example:**
```bash
curl http://localhost:8000/api/conversation-sessions/models/info
```

**Response:**
```json
{
  "sensevoice_loaded": false,
  "sensevoice_model_path": null,
  "tts_engine": "edge-tts",
  "agent_type": "NewsAgent",
  "loading_time_ms": {
    "agent": 150.5
  }
}
```

#### List Sessions

```bash
GET /api/conversation-sessions/sessions?user_id=<user_id>&limit=10
```

---

## Complete Testing Workflow

### 1. Generate Voice Samples

```bash
# Generate test queries as WAV files
edge-tts --text "What's the stock price of AAPL today?" \
  --voice en-US-AriaNeural \
  --write-media tests/voice_samples/test_price_aapl_today.wav

edge-tts --text "What's the latest news about AAPL?" \
  --voice en-US-AriaNeural \
  --write-media tests/voice_samples/test_news_aapl_latest.wav
```

### 2. Compress and Encode

```bash
# Batch compress all samples with OPUS
python tests/testing_utils/voice_encoder.py \
  --batch tests/voice_samples/ \
  --codec opus
```

### 3. Start Backend Server

```bash
# Start the backend
make run-server
```

### 4. Run Comprehensive Test

```bash
# Test multiple queries and validate session
python test_comprehensive_opus.py \
  tests/voice_samples/encoded_compressed_opus/test_price_aapl_today_compressed_opus.json \
  tests/voice_samples/encoded_compressed_opus/test_news_aapl_latest_compressed_opus.json
```

### 5. Validate Results

The test script will:
1. ✅ Connect to WebSocket
2. ✅ Send each audio query
3. ✅ Receive transcription and agent response
4. ✅ Collect TTS audio chunks
5. ✅ Retrieve session data from API
6. ✅ Validate all conversation turns
7. ✅ Generate validation report

---

## Troubleshooting

### Common Issues

#### 1. SenseVoice Model Not Loaded

**Warning:** `⚠️ SenseVoice model not loaded, using fallback transcription`

**Cause:** SenseVoice model directory doesn't exist locally.

**Solution:** This is expected for testing. The backend uses fallback transcription which returns hardcoded test queries. For production, download and configure SenseVoice model.

#### 2. No Session Data Found

**Error:** `Session <id> not found`

**Cause:** Session hasn't been saved yet or was cleaned up.

**Solution:** Wait 1-2 seconds after WebSocket disconnect before querying API. The test script includes this delay.

#### 3. Compression Failed

**Error:** `FFmpeg compression failed`

**Cause:** FFmpeg not installed or not in PATH.

**Solution:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

#### 4. WebSocket Connection Refused

**Error:** `Connection refused`

**Cause:** Backend server not running.

**Solution:**
```bash
make run-server
```

---

## File Organization

```
News_agent/
├── tests/
│   ├── testing_utils/
│   │   ├── voice_encoder.py          # Audio compression & encoding utility
│   │   └── AUDIO_TESTING_GUIDE.md   # This guide
│   └── voice_samples/
│       ├── test_price_nvda_today.wav                    # Original WAV
│       ├── test_news_nvda_latest.wav
│       └── encoded_compressed_opus/
│           ├── test_price_nvda_today_compressed_opus.json    # Compressed + Encoded
│           └── test_news_nvda_latest_compressed_opus.json
├── test_websocket_simple.py          # Basic WebSocket test
├── test_compressed_audio.py          # Compression analysis test
├── test_comprehensive_opus.py        # Multi-query validation test
└── logs/
    └── conversations/
        ├── turns_20251012.jsonl      # Daily conversation log
        ├── session_<id>.json          # Individual session logs
        └── model_info.json            # Model loading logs
```

---

## Best Practices

### 1. Always Use OPUS for Testing

OPUS provides the best compression for speech and is the WebRTC standard. It's what you'll use in production.

### 2. Test Multiple Queries Per Session

Real users will ask multiple questions. Test with 2-3 queries to validate session handling.

### 3. Validate Session Data

Always retrieve and validate session data after testing to ensure complete traceability.

### 4. Check TTS Chunks

Verify TTS chunks were sent correctly - this indicates the full pipeline worked.

### 5. Monitor Model Loading

Check `model_info` API to ensure models are loading as expected in your environment.

### 6. Use Descriptive File Names

Name test files clearly so you can trace back from logs to original test case.

---

## Summary

This testing pipeline provides complete traceability from text query to backend processing:

1. **Text** → Generate voice sample (WAV)
2. **WAV** → Compress with OPUS
3. **OPUS** → Encode to Base64 JSON
4. **JSON** → Send via WebSocket
5. **Backend** → Process and log conversation
6. **API** → Retrieve and validate session
7. **Report** → Verify all data matches expectations

This ensures every conversation can be traced, validated, and debugged throughout the entire audio pipeline.

---

## References

- [OPUS Codec](https://opus-codec.org/) - Official OPUS codec documentation
- [WebRTC](https://webrtc.org/) - Web Real-Time Communication standards
- [Edge-TTS](https://github.com/rany2/edge-tts) - Free text-to-speech using Microsoft Edge
- [FFmpeg](https://ffmpeg.org/) - Audio/video processing toolkit
