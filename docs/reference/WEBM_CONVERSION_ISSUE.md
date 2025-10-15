# WebM Audio Conversion Issue

## Problem Summary

The frontend successfully sends WebM/Opus audio chunks via WebSocket, but the backend cannot convert them to WAV format for transcription.

### Error Message
```
[in#0 @ 0x...] Error opening input: Invalid data found when processing input
Error opening input file /var/folders/.../tmp....webm.
Error opening input files: Invalid data found when processing input
```

### Root Cause

**MediaRecorder chunks are not standalone valid files:**
- `MediaRecorder.start(100)` produces audio chunks every 100ms
- These chunks are WebM container fragments, not complete files
- FFmpeg expects complete, valid WebM files with proper headers
- Individual chunks lack the necessary WebM container structure

## Why This Happens

1. **Frontend** (`ContinuousVoiceInterface.tsx:328`):
   ```typescript
   mediaRecorder.start(100); // Request data every 100ms
   ```

2. **Audio Chunks Collected** (`ondataavailable`):
   ```typescript
   mediaRecorder.ondataavailable = (event) => {
     if (event.data.size > 0) {
       audioChunksRef.current.push(event.data);
     }
   };
   ```

3. **Combined into Blob** (`sendAudioToBackend`):
   ```typescript
   const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
   ```

4. **Backend Attempts Conversion** (`streaming_handler.py:205-235`):
   ```python
   # Create temp file with WebM data
   input_file.write(audio_data)

   # Try to convert with FFmpeg
   ffmpeg -i temp.webm -ar 16000 -ac 1 -f wav output.wav
   ```

5. **FFmpeg Fails:**
   - WebM container structure is incomplete/fragmented
   - Missing proper headers or codec initialization data
   - Cannot decode Opus frames without proper context

## Solutions

### Solution 1: Accumulate Complete WebM File (CURRENT APPROACH)

**Status:** Implemented but not working reliably

The frontend already accumulates chunks before sending, but the combined blob still isn't a valid WebM file.

**Why it fails:**
- WebM container needs proper headers (EBML, Segment, Track info)
- MediaRecorder may not include full headers in every chunk
- Concatenating blobs doesn't create a valid WebM file

### Solution 2: Use WAV Format (RECOMMENDED)

**Problem:** Most browsers don't support WAV in MediaRecorder

**Workaround:** Use Web Audio API to capture PCM data and encode to WAV in browser

#### Implementation Steps:

1. **Capture PCM Data with AudioWorklet:**
   ```javascript
   // Create audio worklet to capture raw PCM
   const audioContext = new AudioContext({ sampleRate: 16000 });
   await audioContext.audioWorklet.addModule('pcm-capture-processor.js');
   const pcmCaptureNode = new AudioWorkletNode(audioContext, 'pcm-capture');
   ```

2. **Encode PCM to WAV:**
   ```javascript
   function encodeWAV(samples, sampleRate = 16000) {
     const buffer = new ArrayBuffer(44 + samples.length * 2);
     const view = new DataView(buffer);

     // WAV header
     writeString(view, 0, 'RIFF');
     view.setUint32(4, 36 + samples.length * 2, true);
     writeString(view, 8, 'WAVE');
     // ... rest of header

     // Write PCM samples
     floatTo16BitPCM(view, 44, samples);

     return buffer;
   }
   ```

3. **Send WAV Data:**
   ```javascript
   const wavBlob = new Blob([wavData], { type: 'audio/wav' });
   const encodedMessage = await audioEncoder.encodeBlob(wavBlob, {
     format: 'wav',
     sampleRate: 16000,
     // ...
   });
   ```

**Pros:**
- WAV files are always valid (simple header + PCM data)
- No conversion needed on backend
- SenseVoice can process directly
- Guaranteed to work

**Cons:**
- Larger file size (no compression)
- More complex frontend code
- Need to implement PCM capture

### Solution 3: Use Whisper.cpp or faster-whisper (ALTERNATIVE)

Instead of SenseVoice, use a transcription model that can handle streaming audio better:

```python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu")
segments, info = model.transcribe(audio_file, beam_size=5)
```

**Pros:**
- Better support for various audio formats
- Can handle incomplete/streaming audio
- More robust error handling

**Cons:**
- Requires different model
- May need API changes

### Solution 4: Buffer Multiple Chunks on Backend

Accumulate multiple audio chunks on the backend before transcription:

```python
class AudioBuffer:
    def __init__(self, session_id):
        self.chunks = []
        self.total_duration = 0

    def add_chunk(self, audio_data):
        self.chunks.append(audio_data)

    def get_complete_audio(self):
        # Combine all chunks into single WebM file
        # Use FFmpeg to concatenate properly
        return combined_audio
```

**Pros:**
- May create more valid WebM files
- Can use FFmpeg concat demuxer

**Cons:**
- Adds latency
- Complex buffering logic
- May still not solve WebM validity issue

## Immediate Workaround

### Test with Existing WAV Files

The project has test WAV files that work correctly:

```bash
ls tests/voice_samples/wav/
# test_price_aapl.wav
# test_news_nvda_latest.wav
# etc.
```

These files demonstrate that the backend transcription pipeline works when given valid WAV files.

### Verify Backend Works

1. **Use test script with WAV file:**
   ```python
   import base64
   import json

   # Read test WAV file
   with open('tests/voice_samples/wav/test_price_aapl.wav', 'rb') as f:
       wav_data = f.read()

   # Encode to base64
   wav_b64 = base64.b64encode(wav_data).decode()

   # Send via WebSocket
   message = {
       "event": "audio_chunk",
       "data": {
           "audio_chunk": wav_b64,
           "format": "wav",
           "is_final": True,
           "session_id": session_id,
           "user_id": user_id,
           "sample_rate": 16000
       }
   }
   ```

2. **Expected Result:**
   - ✅ No FFmpeg errors
   - ✅ Transcription works
   - ✅ Agent responds

## Recommended Path Forward

### Short Term (Immediate Fix)

1. **Switch to WAV encoding in frontend:**
   - Implement Web Audio API PCM capture
   - Create WAV encoder utility
   - Update `sendAudioToBackend()` to use WAV

2. **Update audio encoder:**
   - Add WAV encoding support
   - Keep base64 encoding

3. **Backend changes:**
   - Keep current code
   - WAV files need no conversion

### Long Term (Optimization)

1. **Add Opus support to backend:**
   - Extract Opus frames from WebM
   - Decode Opus directly
   - Skip FFmpeg conversion

2. **Implement proper WebM muxing:**
   - Use WebM library to create valid containers
   - Handle fragmented chunks properly

3. **Consider streaming transcription:**
   - Process audio chunks as they arrive
   - Don't wait for complete utterance

## Files to Modify

### Frontend

1. **Create `frontend/src/utils/wav-encoder.ts`:**
   ```typescript
   export class WAVEncoder {
     encodeFromAudioData(audioData: Float32Array, sampleRate: number): ArrayBuffer {
       // Implement WAV encoding
     }
   }
   ```

2. **Update `frontend/src/components/ContinuousVoiceInterface.tsx`:**
   - Replace MediaRecorder with AudioWorklet
   - Use WAV encoder instead of WebM
   - Update `sendAudioToBackend()` to send WAV

3. **Update `frontend/src/utils/audio-encoder.ts`:**
   - Add WAV format support
   - No compression needed for WAV

### Backend

No changes needed if using WAV format - it already works!

## Testing Plan

1. **Verify current backend with WAV:**
   ```bash
   # Test with existing WAV file
   uv run python test_ws_connection_with_wav.py
   ```

2. **Implement WAV encoding:**
   - Create WAV encoder utility
   - Test PCM capture
   - Verify WAV file validity

3. **Integration test:**
   - Record audio in browser
   - Encode to WAV
   - Send to backend
   - Verify transcription

4. **End-to-end test:**
   - Full voice interaction
   - Multiple utterances
   - Verify quality

## Current Status

- ✅ WebSocket communication works
- ✅ Audio chunks are sent successfully
- ✅ Backend receives data
- ❌ FFmpeg WebM conversion fails
- ✅ Backend transcription works with valid WAV files
- 🔧 Need to implement WAV encoding in frontend

## References

- WebM Format: https://www.webmproject.org/docs/container/
- Web Audio API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- WAV Format: http://soundfile.sapp.org/doc/WaveFormat/
- MediaRecorder API: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder
- FFmpeg WebM: https://trac.ffmpeg.org/wiki/Encode/VP9
