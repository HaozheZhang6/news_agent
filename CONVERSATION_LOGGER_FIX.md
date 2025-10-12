# ConversationLogger Fix - log_speech_detection Method

## Issue

When running `make src`, the following error occurred:

```
ERROR: Audio recording error: 'ConversationLogger' object has no attribute 'log_speech_detection'
```

## Root Cause

The `src/conversation_logger.py` was missing the `log_speech_detection()` method that is called by `src/voice_listener_process.py`.

The method was being called here in voice_listener_process.py:

```python
if vad_result:
    conversation_logger.log_speech_detection(True)  # ❌ Method didn't exist
    last_active_time = time.time()
    segments_to_save.append((raw_audio, time.time()))
else:
    conversation_logger.log_speech_detection(False)  # ❌ Method didn't exist
```

## Fix

Added the missing method to `src/conversation_logger.py`:

```python
def log_speech_detection(self, detected: bool):
    """Log speech detection results (wrapper for log_vad_activity)."""
    # Use debug level to avoid log spam
    status = "Speech detected" if detected else "No speech"
    self.app_logger.debug(f"{status}")
```

**File:** [src/conversation_logger.py](src/conversation_logger.py#L97-L101)

## Why Debug Level?

The method uses `debug` level logging instead of `info` because:
- VAD checks happen every 0.5 seconds
- This would create too much log noise at INFO level
- Debug level keeps logs clean while allowing detailed debugging when needed

## Testing

```bash
# Run the voice agent
make src

# Expected output (no errors):
Starting voice-activated news agent (src.main)...
Starting news agent with parallel threads...
News agent running. Say 'stop' to interrupt, 'tell me more' to dive deeper.
Press Ctrl+C to exit.
2025-10-12 16:03:03,616 - news_agent - INFO - System event: Audio recording started with SenseVoice (using sounddevice)
News speaker started...
2025-10-12 16:03:04,980 - news_agent - INFO - System event: Audio stream opened: 16000Hz, 1 channel(s)

# No more "log_speech_detection" errors!
```

## Related Changes

This fix completes the migration from PyAudio to sounddevice by ensuring all logging methods are present.

---

**Status:** Fixed ✅

**Date:** October 12, 2025

**Impact:** Voice agent now runs without errors
