# VAD Configuration Guide

This guide explains how to configure the backend VAD (Voice Activity Detection) settings.

## Configuration Location

VAD settings are defined in [`backend/app/config.py`](backend/app/config.py) and can be overridden using environment variables.

## Environment Variables

Add these to your `.env` file (e.g., `backend/.env` or `env_files/*.env`):

```bash
# Backend VAD Configuration

# Energy Threshold (RMS - Root Mean Square)
# Default: 500.0
# Range: 0.0 - 5000.0
# Lower = more sensitive (accepts quieter audio)
# Higher = less sensitive (requires louder audio)
VAD_ENERGY_THRESHOLD=500.0

# Speech Ratio Threshold
# Default: 0.03 (3%)
# Range: 0.01 - 0.50
# This is the percentage of audio frames that must contain speech
# Lower = more lenient (accepts audio with more pauses)
# Higher = more strict (requires higher speech density)
VAD_SPEECH_RATIO_THRESHOLD=0.03

# WebRTC VAD Aggressiveness
# Default: 3
# Range: 0-3
# 0 = Least aggressive (most lenient)
# 3 = Most aggressive (most strict)
VAD_AGGRESSIVENESS=3
```

## Detailed Configuration

### 1. VAD_ENERGY_THRESHOLD

**What it does**: First stage filter that checks if audio has sufficient volume/energy.

**Common values**:
- `100.0` - Very sensitive, accepts whispers
- `300.0` - Lenient, accepts quiet speech
- **`500.0` - Normal sensitivity (recommended)** ⭐
- `800.0` - Strict, requires clear/loud speech
- `1000.0` - Very strict, may reject normal speech

**Use cases**:
- **Quiet environment**: Use 300-500
- **Noisy environment**: Use 700-1000
- **Multiple speakers**: Use 400-600

**Example**:
```bash
# For quiet home office
VAD_ENERGY_THRESHOLD=400.0

# For noisy coffee shop
VAD_ENERGY_THRESHOLD=900.0
```

---

### 2. VAD_SPEECH_RATIO_THRESHOLD

**What it does**: Second stage filter that checks what percentage of the audio contains actual speech (not silence/pauses).

**Common values and scenarios**:

#### **0.03 (3%) - Very Lenient [RECOMMENDED]** ⭐
```bash
VAD_SPEECH_RATIO_THRESHOLD=0.03
```
- **Use case**: Natural conversational speech with thinking pauses
- **Accepts**: User speaks 3s, pauses 27s → ✅ ACCEPTED
- **Best for**: Voice assistants, customer service bots, interview agents
- **Why recommended**: Frontend VAD already filters silence, backend should be lenient

#### 0.05 (5%) - Lenient
```bash
VAD_SPEECH_RATIO_THRESHOLD=0.05
```
- **Use case**: Conversational speech with moderate pauses
- **Accepts**: User speaks 5s, pauses 95s → ✅ ACCEPTED
- **Best for**: Casual conversations, Q&A systems

#### 0.10 (10%) - Moderate
```bash
VAD_SPEECH_RATIO_THRESHOLD=0.10
```
- **Use case**: Clear speech with minimal pauses
- **Accepts**: User speaks 5s, pauses 45s → ✅ ACCEPTED
- **Best for**: Dictation, professional recordings

#### 0.15 (15%) - Strict
```bash
VAD_SPEECH_RATIO_THRESHOLD=0.15
```
- **Use case**: Continuous speech with few pauses
- **Accepts**: User speaks 3s, pauses 17s → ✅ ACCEPTED
- **Best for**: Read-aloud, presentations

#### 0.30 (30%) - Very Strict
```bash
VAD_SPEECH_RATIO_THRESHOLD=0.30
```
- **Use case**: High speech density only
- **Accepts**: User speaks 6s, pauses 14s → ✅ ACCEPTED
- **Best for**: Professional voice-overs (**too strict for most use cases**)

---

### 3. VAD_AGGRESSIVENESS

**What it does**: Controls how strict WebRTC VAD is at the frame level when detecting speech vs. non-speech.

**Values**:
- `0` - Least aggressive (detects more as speech, may have false positives)
- `1` - Less aggressive
- `2` - Aggressive
- **`3` - Most aggressive (strictest, fewer false positives)** ⭐ Recommended

**Example**:
```bash
# For noisy environments (stricter detection)
VAD_AGGRESSIVENESS=3

# For quiet environments (more lenient)
VAD_AGGRESSIVENESS=1
```

**Note**: This setting affects frame-level classification, but the overall speech ratio threshold is what determines acceptance.

---

## Configuration Examples

### Example 1: Voice Assistant (Recommended)
```bash
# Natural conversation with pauses
VAD_ENERGY_THRESHOLD=500.0
VAD_SPEECH_RATIO_THRESHOLD=0.03
VAD_AGGRESSIVENESS=3
```

### Example 2: Dictation System
```bash
# Requires clear, continuous speech
VAD_ENERGY_THRESHOLD=600.0
VAD_SPEECH_RATIO_THRESHOLD=0.15
VAD_AGGRESSIVENESS=3
```

### Example 3: Noisy Environment
```bash
# Stricter to filter background noise
VAD_ENERGY_THRESHOLD=900.0
VAD_SPEECH_RATIO_THRESHOLD=0.05
VAD_AGGRESSIVENESS=3
```

### Example 4: Quiet/Sensitive Mode
```bash
# More lenient for soft-spoken users
VAD_ENERGY_THRESHOLD=300.0
VAD_SPEECH_RATIO_THRESHOLD=0.03
VAD_AGGRESSIVENESS=2
```

---

## How to Apply Configuration

### Method 1: Environment File
```bash
# Edit backend/.env or env_files/*.env
VAD_ENERGY_THRESHOLD=500.0
VAD_SPEECH_RATIO_THRESHOLD=0.03
VAD_AGGRESSIVENESS=3
```

### Method 2: Docker/Render Environment Variables
Set these in your deployment platform (Render, Docker, etc.):
- `VAD_ENERGY_THRESHOLD`
- `VAD_SPEECH_RATIO_THRESHOLD`
- `VAD_AGGRESSIVENESS`

### Method 3: Direct Export (Development)
```bash
export VAD_ENERGY_THRESHOLD=500.0
export VAD_SPEECH_RATIO_THRESHOLD=0.03
export VAD_AGGRESSIVENESS=3
uv run python -m uvicorn backend.app.main:app
```

---

## Validation Flow

Understanding how these settings work together:

```
┌─────────────────────┐
│  Incoming Audio     │
│  (from frontend)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│  Stage 1: Energy Check                      │
│  - Calculate RMS energy                     │
│  - Compare with VAD_ENERGY_THRESHOLD        │
│  - If energy < threshold: REJECT ❌         │
└──────────┬──────────────────────────────────┘
           │ PASS ✅
           ▼
┌─────────────────────────────────────────────┐
│  Stage 2: WebRTC VAD Check                  │
│  - Split audio into frames                  │
│  - Classify each frame (speech/non-speech)  │
│    using VAD_AGGRESSIVENESS setting         │
│  - Calculate speech_ratio                   │
│  - Compare with VAD_SPEECH_RATIO_THRESHOLD  │
│  - If ratio < threshold: REJECT ❌          │
└──────────┬──────────────────────────────────┘
           │ PASS ✅
           ▼
┌─────────────────────┐
│  Send to ASR        │
│  (Transcription)    │
└─────────────────────┘
```

---

## Monitoring and Tuning

### Check Logs for VAD Activity

```bash
# Look for acceptance logs
grep "VAD ACCEPTED" logs/backend.log

# Look for rejection logs
grep "VAD REJECTED" logs/backend.log

# Check speech ratio distribution
grep "speech_ratio=" logs/backend.log | awk -F'speech_ratio=' '{print $2}' | awk '{print $1}'
```

### Adjust Based on Metrics

1. **Too many rejections** (users complaining about "No transcription"):
   - Lower `VAD_SPEECH_RATIO_THRESHOLD` (try 0.03 or 0.05)
   - Lower `VAD_ENERGY_THRESHOLD` (try 300-400)

2. **Too many false positives** (noise being transcribed):
   - Raise `VAD_ENERGY_THRESHOLD` (try 700-1000)
   - Raise `VAD_SPEECH_RATIO_THRESHOLD` (try 0.10-0.15)
   - Use `VAD_AGGRESSIVENESS=3`

3. **Inconsistent detection**:
   - Check audio quality from frontend
   - Verify microphone settings
   - Test with different `VAD_AGGRESSIVENESS` values

---

## Testing Configuration

After changing settings, test with:

```bash
# Run VAD tests
python tests/run_vad_tests.py --vad-only -v

# Or specific test
uv run pytest tests/backend/local/core/test_vad_validation.py -v -s
```

---

## Default Configuration Summary

| Setting | Default | Range | Recommended |
|---------|---------|-------|-------------|
| `VAD_ENERGY_THRESHOLD` | 500.0 | 0.0-5000.0 | 300-700 |
| `VAD_SPEECH_RATIO_THRESHOLD` | **0.03** | 0.01-0.50 | **0.03-0.05** |
| `VAD_AGGRESSIVENESS` | 3 | 0-3 | 3 |

**For most use cases, the default values work well! 🎉**

---

## Troubleshooting

### Issue: "VAD REJECTED: No speech detected"
**Cause**: Energy too low
**Solution**: Lower `VAD_ENERGY_THRESHOLD` to 300-400

### Issue: "VAD REJECTED: WebRTC rejected audio"
**Cause**: Speech ratio too low (too much silence)
**Solution**: Lower `VAD_SPEECH_RATIO_THRESHOLD` to 0.03 or 0.02

### Issue: Background noise being transcribed
**Cause**: Thresholds too lenient
**Solution**: Raise `VAD_ENERGY_THRESHOLD` to 700-900

### Issue: Soft-spoken users not detected
**Cause**: Thresholds too strict
**Solution**: Lower all thresholds and use `VAD_AGGRESSIVENESS=2`

---

## Related Documentation

- [VAD Fixes Summary](VAD_FIXES_SUMMARY.md) - Complete VAD fix history
- [VAD Threshold Update](VAD_THRESHOLD_UPDATE.md) - Latest threshold changes
- [VAD Testing Guide](tests/VAD_TESTING_GUIDE.md) - Automated testing framework
- [Config File](backend/app/config.py) - Full configuration with detailed comments

---

**Last Updated**: 2025-10-16
**Configuration Version**: v3 (configurable parameters)