# Current Audio Format & Data Flow

**Last Updated:** 2025-10-14

## Summary

The current implementation uses **WAV format** (16kHz, mono, 16-bit PCM) for frontend-to-backend audio transmission. This replaces the previous WebM/Opus compressed format mentioned in older documentation.

---

## Audio Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AUDIO DATA FLOW                           │
└─────────────────────────────────────────────────────────────┘

[Microphone]
    ↓
[ScriptProcessorNode] → Float32Array chunks (4096 samples)
    ↓
[PCM Buffer] → Store chunks until silence detected
    ↓
[WAV Encoder] → Add 44-byte header + convert to 16-bit PCM
    ↓
[Base64 Encoder] → Encode for WebSocket transmission
    ↓
[WebSocket] → Send to backend
    ↓
[Backend Decode] → Base64 → WAV bytes
    ↓
[HF Space ASR] → Transcription
```

---

## Detailed Implementation

### 1. Frontend Audio Capture

**File:** [frontend/src/utils/wav-encoder.ts](frontend/src/utils/wav-encoder.ts)

**Technology:** Web Audio API with `ScriptProcessorNode`

**Configuration:**
- **Sample Rate:** 16,000 Hz (16kHz)
- **Channels:** 1 (mono)
- **Bit Depth:** 16-bit PCM
- **Buffer Size:** 4,096 samples per chunk

**Process:**
```typescript
// Create audio context with 16kHz sample rate
const audioContext = new AudioContext({ sampleRate: 16000 });
const sourceNode = audioContext.createMediaStreamSource(stream);
const processorNode = audioContext.createScriptProcessor(4096, 1, 1);

// Capture PCM data
processorNode.onaudioprocess = (event) => {
  const inputData = event.inputBuffer.getChannelData(0); // Float32Array
  pcmChunks.push(new Float32Array(inputData));
};
```

### 2. WAV Encoding

**File:** [frontend/src/utils/wav-encoder.ts:28-59](frontend/src/utils/wav-encoder.ts#L28-L59)

**Format:** WAV (RIFF/WAVE container with PCM data)

**WAV Structure:**
```
┌──────────────────────────────────────┐
│ RIFF Header (12 bytes)               │  "RIFF" + size + "WAVE"
├──────────────────────────────────────┤
│ fmt Subchunk (24 bytes)              │  Format info (PCM, 16kHz, mono, 16-bit)
├──────────────────────────────────────┤
│ data Subchunk Header (8 bytes)       │  "data" + PCM data size
├──────────────────────────────────────┤
│ PCM Audio Data (N bytes)             │  16-bit signed integers
└──────────────────────────────────────┘
Total header size: 44 bytes
```

**Encoding Process:**
1. Combine all Float32Array chunks into single array
2. Convert float samples (-1.0 to 1.0) to 16-bit integers
3. Create 44-byte WAV header with format info
4. Combine header + PCM data into ArrayBuffer

### 3. Base64 Encoding

**File:** [frontend/src/utils/audio-encoder.ts:232-251](frontend/src/utils/audio-encoder.ts#L232-L251)

**Method:** `encodeWAV()`

**Process:**
```typescript
// Convert ArrayBuffer to Uint8Array
const bytes = new Uint8Array(wavBuffer);

// Convert to binary string
let binary = '';
for (let i = 0; i < bytes.byteLength; i++) {
  binary += String.fromCharCode(bytes[i]);
}

// Encode to base64
const base64Audio = btoa(binary);
```

**Base64 Overhead:** 33% increase in size (4 bytes base64 per 3 bytes binary)

### 4. WebSocket Transmission

**File:** [frontend/src/components/ContinuousVoiceInterface.tsx:447-459](frontend/src/components/ContinuousVoiceInterface.tsx#L447-L459)

**Message Format:**
```json
{
  "event": "audio_chunk",
  "data": {
    "audio_chunk": "UklGRiQAAA...",     // Base64 encoded WAV
    "format": "wav",                     // Audio format
    "is_final": true,                    // End of utterance
    "session_id": "uuid",                // Session identifier
    "user_id": "uuid",                   // User identifier
    "sample_rate": 16000,                // Sample rate in Hz
    "file_size": 96044                   // WAV file size in bytes
  }
}
```

### 5. Backend Processing

**File:** [backend/app/core/websocket_manager.py:395](backend/app/core/websocket_manager.py#L395)

**Decoding:**
```python
# Decode base64 to bytes
audio_chunk = base64.b64decode(audio_chunk_b64)

# Convert to WAV if needed (already WAV in this case)
wav_data = await self._convert_to_wav(audio_data, format="wav", sample_rate=16000)

# Send to HF Space ASR
transcription = await self.hf_space_asr.transcribe_audio_bytes(
    wav_data,
    sample_rate=16000,
    format="wav"
)
```

---

## File Size Calculations

### Example: 3-Second Voice Recording

**Audio Parameters:**
- Duration: 3 seconds
- Sample rate: 16,000 Hz
- Channels: 1 (mono)
- Bit depth: 16 bits (2 bytes per sample)

**Size Breakdown:**

| Stage | Format | Size | Calculation |
|-------|--------|------|-------------|
| **Memory (Float32)** | Float32Array | 192 KB | 48,000 samples × 4 bytes |
| **PCM Data** | 16-bit PCM | 96 KB | 48,000 samples × 2 bytes |
| **WAV File** | WAV | 96,044 bytes (~94 KB) | 44 bytes header + 96,000 bytes PCM |
| **Base64 Encoded** | String | 128,059 bytes (~125 KB) | 96,044 × 4/3 (base64 overhead) |
| **WebSocket Message** | JSON | ~125.2 KB | Base64 + JSON overhead (~200 bytes) |
| **After Transcription** | Text | ~100-500 bytes | Transcribed text |

**Formula:**
```
PCM samples = Duration × Sample Rate
            = 3 seconds × 16,000 Hz
            = 48,000 samples

PCM size = Samples × Bytes per Sample
         = 48,000 × 2 bytes
         = 96,000 bytes
         = 93.75 KB

WAV file size = Header + PCM
              = 44 bytes + 96,000 bytes
              = 96,044 bytes

Base64 size = WAV size × 4/3
            = 96,044 × 1.333
            = 128,059 bytes
            = 125 KB
```

### Bandwidth Usage

**Per utterance (average 3 seconds):**
- Upload: ~125 KB
- Download (TTS response): ~50-200 KB (depends on response length)

**Per minute of conversation (10 utterances):**
- Upload: ~1.25 MB
- Download: ~1-2 MB
- Total: ~2-3 MB per minute

---

## Comparison with Previous Implementation

The documentation mentions **WebM/Opus** compression, but current code uses **WAV**:

| Metric | Old (WebM/Opus) | Current (WAV) | Change |
|--------|-----------------|---------------|--------|
| **Format** | WebM | WAV | Simpler format |
| **Compression** | Opus codec | None | Removed compression |
| **Sample Rate** | 48 kHz | 16 kHz | Lower rate |
| **File Size (3s)** | ~25 KB | ~94 KB | 3.8x larger |
| **Base64 Size (3s)** | ~33 KB | ~125 KB | 3.8x larger |
| **Encoding Time** | Higher | Lower | Faster encoding |
| **Compatibility** | Browser-dependent | Universal | Better compatibility |
| **Quality** | Higher | Sufficient for speech | Trade-off |

**Why the Change?**
1. **Simplicity:** WAV is universally supported by ASR systems
2. **Reliability:** No codec compatibility issues
3. **Speed:** Faster encoding (no compression step)
4. **Sufficient Quality:** 16kHz is adequate for speech recognition

**Trade-off:**
- 3.8x larger files, but acceptable for:
  - Short utterances (typically 2-5 seconds)
  - Modern internet speeds (125 KB in <0.5s on 2 Mbps)
  - Reduced encoding latency more important than bandwidth

---

## VAD Configuration

**Current Settings:**
```typescript
const SILENCE_THRESHOLD_MS = 700;      // 700ms silence triggers send
const VAD_CHECK_INTERVAL_MS = 250;     // Check every 250ms (4Hz)
const SPEECH_THRESHOLD = 0.02;         // Audio amplitude threshold
const MIN_RECORDING_DURATION_MS = 500; // Minimum utterance length
```

**How it Works:**
1. Continuously capture PCM audio in background
2. Every 250ms, analyze audio amplitude (RMS)
3. If amplitude > 0.02 → speech detected, reset silence timer
4. If amplitude < 0.02 → silence, increment timer
5. After 700ms continuous silence → encode & send WAV

---

## Backend Audio Processing

### HuggingFace Space ASR

**File:** [backend/app/core/hf_space_asr.py:121-156](backend/app/core/hf_space_asr.py#L121-L156)

**Process:**
1. Receive base64 WAV from WebSocket
2. Decode to bytes
3. Write to temporary file
4. Send to HF Space via Gradio client
5. Parse transcription result
6. Clean SenseVoice output tags

**No Additional Processing Needed:**
- WAV format is directly supported
- No format conversion required
- Backend acts as passthrough

---

## Audio Quality Analysis

### 16kHz WAV Quality

**Speech Recognition:**
- ✅ Excellent for speech recognition (human voice: 85-255 Hz fundamentals)
- ✅ Captures harmonics up to 8 kHz (sufficient for speech intelligibility)
- ✅ Standard for telephony and voice recognition

**Comparison:**
- Telephone: 8 kHz (acceptable)
- **Voice AI: 16 kHz (optimal for ASR)**
- Music streaming: 44.1-48 kHz (overkill for speech)

### 16-bit PCM Quality

**Dynamic Range:**
- 16-bit = 96 dB dynamic range
- Human voice: ~60 dB dynamic range
- ✅ More than sufficient for speech

---

## Optimization Opportunities

### Future Improvements

1. **Add Compression (Optional):**
   - Implement Opus compression for bandwidth-constrained scenarios
   - Keep WAV as fallback for compatibility
   - Toggle via `VoiceSettings.audio_compression` flag

2. **Backend Pre-Filtering:**
   - Add energy-based validation before HF Space API call
   - Use WebRTC VAD for more accurate speech detection
   - Reduce unnecessary API calls by 40-60%

3. **Adaptive Quality:**
   - Auto-detect network speed
   - Switch between 16kHz WAV (slow) and 8kHz WAV (very slow)
   - Maintain 16kHz for normal connections

4. **Streaming Chunks:**
   - Stream audio in 1-second chunks instead of full utterance
   - Enable faster transcription start (partial results)
   - Reduce latency by 50-70%

---

## Related Files

### Frontend
- [frontend/src/utils/wav-encoder.ts](frontend/src/utils/wav-encoder.ts) - WAV encoding implementation
- [frontend/src/utils/audio-encoder.ts](frontend/src/utils/audio-encoder.ts) - Base64 encoding utilities
- [frontend/src/components/ContinuousVoiceInterface.tsx](frontend/src/components/ContinuousVoiceInterface.tsx) - Audio capture & VAD

### Backend
- [backend/app/core/websocket_manager.py](backend/app/core/websocket_manager.py) - WebSocket message handling
- [backend/app/core/streaming_handler.py](backend/app/core/streaming_handler.py) - Audio processing
- [backend/app/core/hf_space_asr.py](backend/app/core/hf_space_asr.py) - ASR integration
- [backend/app/config.py](backend/app/config.py) - Audio configuration

### Documentation
- [reference/VAD_FIXES.md](reference/VAD_FIXES.md) - VAD implementation details
- [reference/WAV_IMPLEMENTATION_COMPLETE.md](reference/WAV_IMPLEMENTATION_COMPLETE.md) - WAV migration summary
- [flow.md](flow.md) - Complete system flow (outdated, needs update)

---

## Testing

### Validate WAV Format

```bash
# Test WAV encoding in browser console
const encoder = new WAVEncoder({ sampleRate: 16000 });
const samples = new Float32Array(16000); // 1 second of silence
const wavData = encoder.encodeFromFloat32(samples);

console.log('WAV size:', wavData.byteLength); // Should be 32044 bytes
console.log('Is valid WAV:', WAVUtils.isValidWAV(wavData)); // Should be true
console.log('WAV info:', WAVUtils.getWAVInfo(wavData));
// { sampleRate: 16000, numChannels: 1, bitDepth: 16, duration: 1.0 }
```

### Measure File Sizes

Add logging to measure actual sizes:
```typescript
console.log('PCM samples:', pcmChunks.length);
console.log('WAV size:', wavData.byteLength);
console.log('Base64 size:', base64Audio.length);
console.log('Compression ratio:', base64Audio.length / wavData.byteLength);
```

---

## Conclusion

The current implementation prioritizes **simplicity, reliability, and speed** over **bandwidth efficiency**. For typical voice interactions (2-5 second utterances), the 125 KB file size is acceptable and provides:

- ✅ Universal format compatibility (WAV)
- ✅ Fast encoding (no compression step)
- ✅ Sufficient quality (16kHz, 16-bit)
- ✅ Reliable transmission (no codec issues)

Future optimizations can add optional compression without breaking existing functionality.