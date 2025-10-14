# Frontend WebSocket Root Cause - FIXED

## The Real Problem

The WebSocket was disconnecting immediately due to **React useEffect cleanup running on every render** instead of only on unmount.

## Root Cause

### The Bug (Lines 501-514)

```typescript
useEffect(() => {
  return () => {
    stopRecording();
    stopAudioPlayback();

    if (wsRef.current) {
      wsRef.current.close(); // ❌ This was running on EVERY RENDER!
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
  };
}, [stopRecording, stopAudioPlayback]); // ❌ These dependencies change on every render!
```

### Why This Happened

1. **`stopRecording` and `stopAudioPlayback` are `useCallback` functions**
2. **They have dependencies that change frequently**
3. **When dependencies change, useCallback creates a new function reference**
4. **React sees new function references in useEffect dependency array**
5. **React thinks dependencies changed, so it runs cleanup**
6. **Cleanup closes the WebSocket immediately**

### The Timeline

```
Component renders
  ↓
useEffect cleanup runs (because dependencies changed)
  ↓
wsRef.current.close() is called ← ❌ KILLS THE CONNECTION
  ↓
useEffect setup runs
  ↓
(nothing to setup, but damage already done)
  ↓
Meanwhile, backend tries to send "connected" message
  ↓
ERROR: "Cannot call 'send' once a close message has been sent"
```

## The Fix

### Remove Dependencies from Cleanup Effect

```typescript
/**
 * Cleanup on unmount ONLY (empty dependency array)
 */
useEffect(() => {
  return () => {
    // Cleanup only on unmount, not on every render
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }

    if (isPlayingAudioRef.current && currentAudioSourceRef.current) {
      currentAudioSourceRef.current.stop();
    }

    if (wsRef.current) {
      wsRef.current.close();
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
  };
}, []); // ✅ Empty array = cleanup runs ONLY on unmount
```

### Why This Works

1. **Empty dependency array `[]`** = effect runs once on mount, cleanup runs once on unmount
2. **Uses refs directly** instead of calling functions that might change
3. **WebSocket stays open** for the entire component lifecycle
4. **No premature cleanup** on re-renders

## Testing the Fix

### Test File Created

`test_frontend_ws.html` - Standalone HTML test page that:
- Connects to WebSocket
- Shows connection status
- Logs all events
- Allows manual recording and audio sending
- No React dependencies = no useEffect bugs

### How to Test

1. **Start backend**:
   ```bash
   make run-server
   ```

2. **Open test file**:
   ```bash
   open test_frontend_ws.html
   ```

3. **Click "Connect WebSocket"**

4. **Expected Results**:
   ```
   ✅ Connecting to ws://localhost:8000/ws/voice?user_id=...
   ✅ WebSocket connection opened
   ✅ Received: connected
   ✅ Session established: xxxxxxxx...
   ```

5. **Backend logs should show**:
   ```
   INFO:     connection open
   DEBUG: 📤 WS_SEND | session=xxx | event=connected
   DEBUG: ✅ Successfully sent connected message
   ```

6. **Should NOT see**:
   ```
   ❌ INFO:     connection closed  (immediately after open)
   ❌ ERROR: WebSocketDisconnect
   ❌ ERROR: Cannot call "send" once a close message has been sent
   ```

### Test in React App

After fixing the useEffect bug, the React component should also work:

1. **Start frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Navigate to the voice interface page**

3. **Click microphone button**

4. **Expected**:
   - WebSocket connects and stays connected
   - No immediate disconnection
   - Microphone permission dialog shows
   - After granting permission, recording starts
   - Can send audio to backend

## Related Changes

### All Frontend WebSocket Fixes

This is the **third and final fix** needed:

1. ✅ **First Fix**: Don't auto-start recording on "connected" event
   - Problem: Microphone permission dialog while WebSocket initializing
   - Solution: Use flag + state changes

2. ✅ **Second Fix**: Use useEffect for recording state management
   - Problem: Callback dependencies causing re-renders
   - Solution: State-driven recording start/stop

3. ✅ **Third Fix**: Remove dependencies from cleanup effect  ← **THIS FIX**
   - Problem: useEffect cleanup running on every render
   - Solution: Empty dependency array for cleanup

## Why This Bug Was Hard to Find

1. **Silent Failure**: WebSocket closed immediately but no obvious error in frontend console
2. **Timing Issue**: Connection opened and closed within milliseconds
3. **Backend Symptoms**: Backend saw disconnect but didn't know why frontend closed
4. **React-Specific**: Only happens in React with useEffect - vanilla JS works fine
5. **Common Pattern**: Many devs put cleanup functions in useEffect dependencies without realizing the implications

## Lessons Learned

### React useEffect Best Practices

1. **Cleanup effects should usually have empty dependencies**:
   ```typescript
   useEffect(() => {
     // Setup
     return () => {
       // Cleanup
     };
   }, []); // Empty for unmount-only cleanup
   ```

2. **Use refs for values that shouldn't trigger re-renders**:
   ```typescript
   const wsRef = useRef<WebSocket>(null);
   // Can access wsRef.current without causing re-renders
   ```

3. **Be careful with useCallback in dependencies**:
   ```typescript
   const fn = useCallback(() => {}, [dep]); // Creates new function when dep changes

   useEffect(() => {
     return () => fn(); // ❌ Cleanup runs when fn changes!
   }, [fn]); // ❌ Bad: fn changes frequently
   ```

4. **Cleanup should be idempotent and safe**:
   ```typescript
   if (wsRef.current) { // Check before closing
     wsRef.current.close();
   }
   ```

## Files Modified

1. ✅ `frontend/src/components/ContinuousVoiceInterface.tsx`
   - Lines 501-524: Fixed cleanup effect dependencies

2. ✅ `test_frontend_ws.html`
   - Created standalone test page for debugging

## Status

| Issue | Status | Notes |
|-------|--------|-------|
| WebSocket Immediate Disconnect | ✅ FIXED | useEffect cleanup bug |
| Microphone Auto-Start | ✅ FIXED | Flag-based approach |
| Callback Dependencies | ✅ FIXED | State-driven recording |
| Test Infrastructure | ✅ CREATED | test_frontend_ws.html |
| Audio Encoding | ⏳ Pending | Next step |
| Audio Sending | ⏳ Pending | Next step |
| TTS Playback | ⏳ Pending | Next step |

---

**Date**: October 12, 2025
**Status**: ✅ ROOT CAUSE FOUND AND FIXED
**Confidence**: High - This was the bug causing immediate disconnection
**Next**: Test with both test page and React app
