# VAD Threshold Update: 0.03 (3%)

## Summary

Updated backend VAD speech ratio threshold from **0.15 (15%)** to **0.03 (3%)** to be more lenient with audio that contains long pauses. Also improved logging to clearly show when audio is accepted vs rejected.

---

## Changes Made

### 1. **Lowered Speech Ratio Threshold**
**File**: [backend/app/core/audio_validator.py:139-142](backend/app/core/audio_validator.py#L139-L142)

```python
# Before (15% threshold):
# Require at least 15% speech frames
is_valid = speech_ratio >= 0.15

# After (3% threshold):
# Require at least 3% speech frames (very lenient to accommodate
# frontend VAD which sends audio with significant silence padding)
# This allows audio with long pauses to pass validation
is_valid = speech_ratio >= 0.03
```

**Reasoning**:
- Frontend sends complete audio chunks that include silence before/after speech
- Users may have natural pauses in their speech
- 3% threshold is very lenient while still filtering out pure silence/noise

---

### 2. **Improved VAD Logging**
**File**: [backend/app/core/streaming_handler.py:182-200](backend/app/core/streaming_handler.py#L182-L200)

#### Added Acceptance Logging
```python
# New logging when audio is ACCEPTED
else:
    print(f"✅ VAD ACCEPTED: Audio validated (energy={energy:.1f}, speech_ratio={speech_ratio:.2f}, size={len(audio_data)} bytes)")
```

#### Improved Rejection Logging
```python
# Before:
print(f"🤫 VAD: WebRTC rejected audio (speech_ratio={speech_ratio:.2f})")

# After:
print(f"🚫 VAD REJECTED: WebRTC rejected audio (speech_ratio={speech_ratio:.2f}, threshold=0.03)")
```

**Benefits**:
- ✅ Clear visibility when audio passes validation
- ✅ Shows exact threshold in rejection messages
- ✅ Consistent emoji usage (🚫 for rejection, ✅ for acceptance)
- ✅ Includes audio size for debugging

---

### 3. **Updated Tests**
**File**: [tests/backend/local/core/test_vad_validation.py:128-160](tests/backend/local/core/test_vad_validation.py#L128-L160)

```python
# Renamed and updated test
def test_speech_ratio_threshold_3_percent(self, audio_samples):
    """Test that 3% speech ratio threshold is working (very lenient)."""
    # Tests samples with 3-30% speech ratio
    if 0.03 <= speech_ratio < 0.30:
        # These now pass validation
```

---

## Expected Behavior

### Before Changes (15% threshold)

```
🎤 Processing audio chunk: 319532 bytes (wav)
🤫 VAD: WebRTC rejected audio (speech_ratio=0.20)  ❌ REJECTED
🎤 Processing result: {'success': False, 'error': 'No transcription'}
```

**Result**: Audio with 20% speech ratio was rejected

---

### After Changes (3% threshold)

```
🎤 Processing audio chunk: 319532 bytes (wav)
✅ VAD ACCEPTED: Audio validated (energy=1234.5, speech_ratio=0.20, size=319532 bytes)  ✅ ACCEPTED
🌐 Using HF Space ASR: 319532 bytes (wav)
✓ HF Space transcribed: 'what is the price of apple'
🎤 Processing result: {'success': True, 'transcription': 'what is the price of apple', ...}
```

**Result**: Audio with 20% speech ratio now passes validation

---

## Validation Thresholds Comparison

| Threshold | Speech Ratio Range | Use Case |
|-----------|-------------------|----------|
| 0.30 (30%) | High speech density | Original (too strict) |
| 0.15 (15%) | Medium speech density | Previous update |
| **0.03 (3%)** | Very lenient | **Current (recommended)** |

### Speech Ratio Examples

- **0.50 (50%)**: User speaks for 5 seconds, 5 seconds silence → **Passes all thresholds**
- **0.25 (25%)**: User speaks for 2.5 seconds, 7.5 seconds silence → **Passes 15% and 3%**
- **0.20 (20%)**: User speaks for 2 seconds, 8 seconds silence → **Passes 3% only** ⭐
- **0.10 (10%)**: User speaks for 1 second, 9 seconds silence → **Passes 3% only** ⭐
- **0.02 (2%)**: Mostly silence, very little speech → **Rejected**

---

## Testing

### Run VAD Tests

```bash
# Test the new 3% threshold
uv run pytest tests/backend/local/core/test_vad_validation.py::TestVADValidation::test_speech_ratio_threshold_3_percent -v -s

# Run all VAD tests
python tests/run_vad_tests.py --vad-only -v
```

### Expected Test Output

```
test_speech_ratio_threshold_3_percent PASSED
✓ Found X samples with 3-30% speech ratio
  These samples now pass validation with 3% threshold (very lenient)
```

---

## Impact

### Positive Effects

1. **Higher Acceptance Rate**: More audio with natural pauses will be accepted
2. **Better User Experience**: Less "No transcription" errors
3. **Clearer Logging**: Easy to see why audio was accepted/rejected
4. **Debugging**: Audio size and metrics visible in logs

### Potential Concerns

1. **False Positives**: Very quiet speech or noise might pass (3% is lenient)
2. **Energy Threshold**: First line of defense (500.0 RMS) still filters pure silence

### Mitigation

The **two-stage validation** provides protection:

```
Stage 1: Energy Threshold (500.0 RMS)
   ↓ Filters out pure silence/very quiet audio

Stage 2: WebRTC VAD (3% speech ratio)
   ↓ Filters out noise/non-speech audio

Result: Accept only audio with both sufficient energy AND some speech content
```

---

## Monitoring

After deploying this change, monitor:

### Success Metrics
- ✅ Reduction in "No transcription" errors
- ✅ Increase in successful voice interactions
- ✅ User satisfaction with voice recognition

### Watch For
- ⚠️ False positives (noise being transcribed)
- ⚠️ Transcription quality issues
- ⚠️ Unexpected audio acceptance

### Logs to Check

```bash
# Look for acceptance logs
grep "VAD ACCEPTED" backend.log

# Look for rejection logs
grep "VAD REJECTED" backend.log

# Check speech ratio distribution
grep "speech_ratio=" backend.log | awk -F'speech_ratio=' '{print $2}' | awk '{print $1}'
```

---

## Rollback Plan

If 3% is too lenient, you can adjust back:

### Option 1: Revert to 15%
```python
# In backend/app/core/audio_validator.py
is_valid = speech_ratio >= 0.15
```

### Option 2: Try 10% (middle ground)
```python
# In backend/app/core/audio_validator.py
is_valid = speech_ratio >= 0.10
```

### Option 3: Make it Configurable
```python
# Add to VoiceSettings model
backend_speech_ratio_threshold: float = Field(default=0.03, ge=0.01, le=0.50)
```

---

## Summary of All VAD Fixes

| Fix | File | Description |
|-----|------|-------------|
| Frontend VAD | `ContinuousVoiceInterface.tsx:574-588` | Keep VAD active during agent speech |
| Backend Threshold (v1) | `audio_validator.py` | Lowered from 30% to 15% |
| **Backend Threshold (v2)** | **`audio_validator.py`** | **Lowered from 15% to 3%** ⭐ |
| **Improved Logging** | **`streaming_handler.py`** | **Added acceptance logging** ⭐ |
| Test Updates | `test_vad_validation.py` | Updated test for 3% threshold |

---

## Recommendation

✅ **Deploy the 3% threshold** and monitor for 24-48 hours.

The combination of:
- Energy threshold (500.0 RMS) for pre-filtering
- Very lenient speech ratio (3%) for final validation
- Clear acceptance/rejection logging

Should provide the best balance between accepting natural speech with pauses and filtering out pure noise/silence.

---

## Files Modified

1. ✅ `backend/app/core/audio_validator.py` - Threshold 0.15 → 0.03
2. ✅ `backend/app/core/streaming_handler.py` - Added acceptance logging
3. ✅ `tests/backend/local/core/test_vad_validation.py` - Updated test name and logic
4. ✅ `VAD_THRESHOLD_UPDATE.md` - This documentation

**Date**: 2025-10-16
**Version**: v2 (3% threshold)
