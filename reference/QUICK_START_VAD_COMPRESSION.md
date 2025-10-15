# Quick Start: VAD Configuration & Audio Compression

**Get started with configurable VAD and Opus compression in 5 minutes**

---

## Overview

This guide will help you:
1. Configure VAD settings for your environment
2. Enable Opus compression to save 80% bandwidth
3. Test the new features

---

## Option 1: Quick Start (Default Settings)

**No configuration needed!** The system works with sensible defaults:

- VAD threshold: `0.02` (moderate sensitivity)
- Silence timeout: `700ms` (fast response)
- Backend validation: Enabled
- Audio format: WAV (uncompressed)

Just start the app and it works!

---

## Option 2: Enable Opus Compression (Recommended for Mobile)

### Frontend (React)

Add to your voice component:

```typescript
import { useVoiceSettings } from '../hooks/useVoiceSettings';

function MyVoiceComponent() {
  const { updateSetting } = useVoiceSettings();

  // Enable Opus compression on component mount
  useEffect(() => {
    updateSetting('use_compression', true);
  }, []);

  return <ContinuousVoiceInterface userId={userId} />;
}
```

**Benefits:**
- 3-second audio: 94 KB → 18 KB (5.2x smaller)
- Faster transmission on slow connections
- Same speech quality

---

## Option 3: Adjust VAD for Your Environment

### Quiet Environment (Office, Library)

```typescript
import { VAD_PRESETS } from '../types/voice-settings';

const { saveSettings } = useVoiceSettings();

// Apply sensitive preset
saveSettings(VAD_PRESETS.sensitive);
```

**Settings:**
- Lower VAD threshold (0.01) - detects whispers
- Faster response (500ms silence)
- Less strict validation

### Noisy Environment (Coffee Shop, Street)

```typescript
// Apply strict preset
saveSettings(VAD_PRESETS.strict);
```

**Settings:**
- Higher VAD threshold (0.03) - filters noise
- Longer silence timeout (1000ms)
- Strictest backend validation

---

## Option 4: Custom Configuration

### Frontend

```typescript
const { updateSetting } = useVoiceSettings();

// Adjust individual settings
updateSetting('vad_threshold', 0.025);
updateSetting('silence_timeout_ms', 800);
updateSetting('use_compression', true);
updateSetting('compression_bitrate', 128000); // Higher quality
```

### Backend (via API)

```bash
# Update settings for user
curl -X PUT "http://localhost:8000/api/voice-settings/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "vad_threshold": 0.025,
    "silence_timeout_ms": 800,
    "use_compression": true,
    "backend_vad_enabled": true,
    "backend_vad_mode": 3
  }'
```

---

## Testing Your Configuration

### 1. Test VAD Sensitivity

Open browser console and watch for:

```
🎙️ Audio level: 0.0234 (threshold: 0.02)  ← Speaking detected
🤐 Silence: 0.7s, recorded: 2.35s          ← Silence detected
📤 Silence threshold reached                ← Sending audio
```

**Too sensitive?** (Detects keyboard clicks, breathing)
- Increase threshold: `updateSetting('vad_threshold', 0.03)`

**Not sensitive enough?** (Misses soft speech)
- Decrease threshold: `updateSetting('vad_threshold', 0.015)`

### 2. Test Compression

Check WebSocket messages in Network tab:

**Without compression:**
```
📤 Sent WAV audio: 96044 bytes (uncompressed)
```

**With compression:**
```
📤 Sent Opus audio: 18230 bytes (compressed)
```

### 3. Test Backend Validation

Check server logs for validation results:

```
✅ Audio validated: energy=2345.1, speech_ratio=0.87
```

or

```
🚫 Audio rejected: insufficient_energy (energy=123.4 < 500.0)
```

---

## Common Use Cases

### Mobile App (Slow Connection)

```typescript
saveSettings({
  vad_threshold: 0.02,           // Balanced
  silence_timeout_ms: 700,       // Fast
  use_compression: true,         // Essential!
  compression_codec: 'opus',
  compression_bitrate: 64000,    // 5x compression
  backend_vad_enabled: true,     // Filter noise
  backend_vad_mode: 2,           // Balanced
});
```

**Result:** ~240 KB/minute vs ~1.25 MB/minute (80% savings)

### Desktop App (Fast Connection, Quiet)

```typescript
saveSettings({
  vad_threshold: 0.01,           // Very sensitive
  silence_timeout_ms: 500,       // Very fast
  use_compression: false,        // Quality over size
  backend_vad_enabled: true,
  backend_vad_mode: 0,           // Least strict
});
```

**Result:** Best quality, lowest latency

### Call Center (Noisy Background)

```typescript
saveSettings({
  vad_threshold: 0.03,           // High threshold
  silence_timeout_ms: 1000,      // Wait longer
  use_compression: true,         // Save bandwidth
  backend_vad_enabled: true,
  backend_vad_mode: 3,           // Strictest validation
  backend_energy_threshold: 800, // High energy required
});
```

**Result:** Filters background noise, only transcribes clear speech

---

## Monitoring & Debugging

### Check Current Settings

```typescript
import { useVoiceSettings } from '../hooks/useVoiceSettings';

const { settings } = useVoiceSettings();
console.log('Current settings:', settings);
```

### Reset to Defaults

```typescript
const { resetSettings } = useVoiceSettings();
resetSettings();
```

or via API:

```bash
curl -X DELETE "http://localhost:8000/api/voice-settings/user123"
```

### View Available Presets

```bash
curl "http://localhost:8000/api/voice-settings/user123/presets"
```

Response:
```json
{
  "sensitive": { "vad_threshold": 0.01, ... },
  "balanced": { "vad_threshold": 0.02, ... },
  "strict": { "vad_threshold": 0.03, ... }
}
```

---

## Performance Metrics

### Latency Impact

| Configuration | Total Latency | Notes |
|---------------|---------------|-------|
| WAV + No Validation | 646-1291ms | Baseline |
| WAV + Validation | 652-1302ms | +6-11ms for validation |
| Opus + Validation | 566-1091ms | **80-200ms faster!** |

### Bandwidth Usage

| Format | Per 3s | Per Minute | Per Hour |
|--------|--------|------------|----------|
| WAV | 125 KB | 1.25 MB | 75 MB |
| Opus (64kbps) | 24 KB | 240 KB | 14 MB |
| **Savings** | **101 KB** | **1 MB** | **61 MB** |

---

## Troubleshooting

### Audio Always Rejected

**Symptom:** Console shows "Audio validation failed: insufficient_energy"

**Solution:**
```typescript
updateSetting('backend_energy_threshold', 200);  // Lower threshold
updateSetting('backend_vad_enabled', false);     // Disable temporarily
```

### Opus Not Working

**Symptom:** Console shows "Opus not supported, using WAV"

**Check browser support:**
```typescript
console.log('Opus WebM:', MediaRecorder.isTypeSupported('audio/webm;codecs=opus'));
```

**Solution:**
- Use Chrome, Firefox, or Edge (Safari has limited support)
- Fallback to WAV automatically happens

### VAD Too Sensitive

**Symptom:** Sends audio on keyboard clicks, breathing, noise

**Solution:**
```typescript
updateSetting('vad_threshold', 0.03);
updateSetting('backend_vad_mode', 3);
updateSetting('backend_energy_threshold', 800);
```

---

## API Reference

### GET /api/voice-settings/{user_id}

Get user's voice settings.

```bash
curl "http://localhost:8000/api/voice-settings/user123"
```

### PUT /api/voice-settings/{user_id}

Update settings.

```bash
curl -X PUT "http://localhost:8000/api/voice-settings/user123" \
  -H "Content-Type: application/json" \
  -d '{"vad_threshold": 0.03, "use_compression": true}'
```

### GET /api/voice-settings/{user_id}/presets

Get VAD presets.

```bash
curl "http://localhost:8000/api/voice-settings/user123/presets"
```

### GET /api/voice-settings/{user_id}/compression-info

Get compression format information.

```bash
curl "http://localhost:8000/api/voice-settings/user123/compression-info"
```

---

## Next Steps

1. **Test in Production**
   - Deploy to Render/Vercel
   - Test with real mobile devices
   - Monitor bandwidth usage

2. **Create UI Settings Panel**
   - Add sliders for VAD threshold
   - Toggle for compression
   - Preset buttons (sensitive/balanced/strict)

3. **Collect Metrics**
   - Track compression ratios
   - Monitor validation rejection rates
   - Measure latency improvements

4. **Optimize Further**
   - Implement adaptive VAD (auto-calibrate to environment)
   - Add quality metrics dashboard
   - Support additional codecs (AAC, Speex)

---

## Resources

- [Full Documentation](VAD_AND_COMPRESSION_GUIDE.md)
- [Audio Format Details](AUDIO_FORMAT_CURRENT.md)
- [API Documentation](../backend/README.md)
- [Frontend Components](../frontend/src/components/ContinuousVoiceInterface.tsx)

---

**Questions?** Check the [full VAD & Compression Guide](VAD_AND_COMPRESSION_GUIDE.md) for detailed information.
