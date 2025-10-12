# Logging Guide

## Log File Locations

### Backend Logs
**Location**: `logs/detailed/backend_{YYYYMMDD}_{HHMMSS}.log`

**Example**: `logs/detailed/backend_20251011_231837.log`

**Format**: 
- `YYYYMMDD`: Date (e.g., 20251011 = October 11, 2025)
- `HHMMSS`: Time when backend started (e.g., 231837 = 23:18:37)

**New log created**: Every time the backend server starts

### Frontend Logs
**Location**: Browser localStorage with key `frontend_{YYYYMMDD}_{HHMMSS}`

**Example**: `frontend_20251011_231845`

**Format**:
- `YYYYMMDD`: Date
- `HHMMSS`: Time when frontend session started

**New log created**: First time you open the frontend in a browser session

---

## Viewing Logs

### Backend Logs

#### View Latest Log
```bash
# List all backend logs (newest first)
ls -lt logs/detailed/backend_*.log | head -5

# View latest log
tail -50 logs/detailed/backend_20251011_231837.log

# Watch in real-time
tail -f logs/detailed/backend_20251011_231837.log

# Search for specific session
grep "abc12345" logs/detailed/backend_20251011_231837.log

# Count errors
grep "ERROR" logs/detailed/backend_20251011_231837.log | wc -l
```

#### Log Levels
- **DEBUG**: All events (VAD, audio chunks, every message)
- **INFO**: Important events (connections, transcriptions, responses)
- **WARNING**: Non-critical issues (throttled errors)
- **ERROR**: Critical failures

### Frontend Logs

#### View in Browser Console
1. Open DevTools (F12)
2. Console tab
3. See colored, real-time logs

#### View in LocalStorage
```javascript
// In browser console:

// Get current session timestamp
const session = localStorage.getItem('frontend_log_session');
console.log('Current session:', session);

// Get all logs for this session
const logs = JSON.parse(localStorage.getItem(`frontend_${session}`));
console.log('Total logs:', logs.length);

// View recent logs
console.table(logs.slice(-20));

// Filter by category
const wsLogs = logs.filter(log => log.category === 'ws');
const audioLogs = logs.filter(log => log.category === 'audio');
const errorLogs = logs.filter(log => log.level === 'error');

// Export logs
logger.downloadLogs();  // Downloads frontend_{timestamp}.json
```

#### View All Sessions
```javascript
// List all frontend log sessions in localStorage
Object.keys(localStorage)
  .filter(key => key.startsWith('frontend_'))
  .forEach(key => {
    const logs = JSON.parse(localStorage.getItem(key));
    console.log(`${key}: ${logs.length} logs`);
  });
```

---

## Log Format

### Backend Log Format
```
YYYY-MM-DD HH:MM:SS.mmm | LEVEL | logger_name | emoji CATEGORY | message
```

**Example**:
```
2025-10-11 23:18:45.123 | INFO  | voice_agent | 🔌 WS_CONNECT | session=abc12345... | user=def67890...
2025-10-11 23:18:45.124 | DEBUG | voice_agent | 📤 WS_SEND | session=abc12345... | event=connected
2025-10-11 23:18:46.234 | INFO  | voice_agent | 📝 TRANSCRIPTION | session=abc12345... | text='What's the...'
```

### Frontend Log Format
```json
{
  "timestamp": "2025-10-11T23:18:45.123Z",
  "level": "info",
  "category": "ws",
  "message": "Connected | session=abc12345...",
  "data": {...}
}
```

---

## Log Categories

### Backend Categories
| Emoji | Category | Description |
|-------|----------|-------------|
| 🔌 | WS_CONNECT | WebSocket connection established |
| 🔌 | WS_DISCONNECT | WebSocket disconnected |
| 📥 | WS_RECV | WebSocket message received |
| 📤 | WS_SEND | WebSocket message sent |
| 🎤 | AUDIO_RECV | Audio chunk received from frontend |
| 🔊 | AUDIO_SEND | Audio chunk sent to frontend |
| 📝 | TRANSCRIPTION | Speech-to-text result |
| 🤖 | LLM_RESPONSE | Agent response |
| 🛑 | INTERRUPT | User interrupted agent |
| ❌ | ERROR | Error occurred |
| ⚠️ | WARNING | Warning message |
| ℹ️ | INFO | General information |
| 🔍 | DEBUG | Debug information |

### Frontend Categories
| Emoji | Category | Description |
|-------|----------|-------------|
| 🔌 | ws | WebSocket events |
| 🎤 | audio | Audio recording |
| 📊 | vad | Voice Activity Detection |
| 🔊 | playback | Audio playback |
| 📝 | transcription | Transcription received |
| 🤖 | response | Agent response received |
| 🛑 | interrupt | Interruption events |
| ❌ | error | Errors |
| ⚠️ | warning | Warnings |
| ℹ️ | info | General info |
| 🔍 | debug | Debug info |

---

## Common Log Patterns

### Successful Connection
**Backend**:
```
🔌 WS_CONNECT | session=abc12345... | user=def67890...
📤 WS_SEND | session=abc12345... | event=connected
```

**Frontend**:
```
🔌 ws | Connecting to ws://localhost:8000/ws/voice?user_id=...
🔌 ws | Connected | session=abc12345...
🎤 audio | Recording started with VAD
```

### Successful Voice Command
**Frontend**:
```
📊 vad | Speech detected
📊 vad | Silence detected | duration=1000ms
ℹ️ vad | Silence threshold reached → sending audio
📤 ws | 📤 SEND | event=audio_chunk | session=abc12345...
```

**Backend**:
```
📥 WS_RECV | session=abc12345... | event=audio_chunk
🎤 AUDIO_RECV | session=abc12345... | size=153600 bytes
📝 TRANSCRIPTION | session=abc12345... | text='What's the stock...'
🤖 LLM_RESPONSE | session=abc12345... | text='The current price...'
📤 WS_SEND | session=abc12345... | event=agent_response
🔊 AUDIO_SEND | session=abc12345... | chunk=0
🔊 AUDIO_SEND | session=abc12345... | chunk=1
...
```

**Frontend**:
```
📥 ws | 📥 RECV | event=transcription | session=abc12345...
📝 transcription | "What's the stock price of AAPL?"
📥 ws | 📥 RECV | event=agent_response | session=abc12345...
🤖 response | "The current price of Apple stock is..."
📥 ws | 📥 RECV | event=tts_chunk | session=abc12345...
🔊 playback | TTS playback started
```

### Interruption
**Frontend**:
```
📊 vad | Speech detected
🛑 playback | 🛑 Playback interrupted by user speech
📤 ws | 📤 SEND | event=interrupt | session=abc12345...
```

**Backend**:
```
📥 WS_RECV | session=abc12345... | event=interrupt
🛑 INTERRUPT | session=abc12345... | reason=user_started_speaking
📤 WS_SEND | session=abc12345... | event=streaming_interrupted
```

### Connection Error
**Backend**:
```
❌ ERROR | session=abc12345... | type=send_message_failed | msg=...
⚠️ WARNING | session=abc12345... | msg=WebSocket not found, skipping message
```

---

## Cleaning Up Old Logs

### Backend Logs
```bash
# Delete logs older than 7 days
find logs/detailed -name "backend_*.log" -mtime +7 -delete

# Keep only last 10 logs
ls -t logs/detailed/backend_*.log | tail -n +11 | xargs rm -f

# Archive old logs
tar -czf logs/archive/backend_logs_$(date +%Y%m).tar.gz logs/detailed/backend_*.log
```

### Frontend Logs
```javascript
// Clear all frontend logs from localStorage
Object.keys(localStorage)
  .filter(key => key.startsWith('frontend_'))
  .forEach(key => localStorage.removeItem(key));

// Clear current session
const session = localStorage.getItem('frontend_log_session');
localStorage.removeItem(`frontend_${session}`);
localStorage.removeItem('frontend_log_session');
```

---

## Debugging Tips

### Find Specific Session
**Backend**:
```bash
# Find all logs for a specific session ID
grep "abc12345" logs/detailed/backend_*.log

# Find all errors for a session
grep "abc12345" logs/detailed/backend_*.log | grep "ERROR"

# Timeline of events for a session
grep "abc12345" logs/detailed/backend_*.log | sort
```

**Frontend**:
```javascript
// Filter logs for specific session_id
const sessionLogs = logs.filter(log => 
  log.message.includes('abc12345') || 
  log.data?.session_id?.startsWith('abc12345')
);
console.table(sessionLogs);
```

### Performance Analysis
```bash
# Backend: Find slow operations
grep "processing_time" logs/detailed/backend_*.log

# Backend: Count messages by type
grep "WS_RECV" logs/detailed/backend_*.log | \
  sed 's/.*event=//' | sort | uniq -c

# Backend: Find gaps in timestamps (potential freezes)
awk '{print $2}' logs/detailed/backend_*.log | \
  uniq -c | awk '$1 > 100'
```

### Error Analysis
```bash
# Count errors by type
grep "ERROR" logs/detailed/backend_*.log | \
  sed 's/.*type=//' | cut -d'|' -f1 | sort | uniq -c

# Find most common warnings
grep "WARNING" logs/detailed/backend_*.log | \
  sed 's/.*msg=//' | sort | uniq -c | sort -rn | head -10
```

---

## Log Rotation

### Automatic Rotation (Recommended)

**Backend**: New log file created on each server start
- No manual rotation needed
- Old logs accumulate in `logs/detailed/`
- Use cron job or script to archive/delete old logs

**Frontend**: New session per browser session
- LocalStorage has 5-10MB limit
- Old sessions need manual cleanup
- Consider adding auto-cleanup code

### Manual Cleanup Script
```bash
#!/bin/bash
# cleanup_logs.sh

# Keep only last 30 days of backend logs
find logs/detailed -name "backend_*.log" -mtime +30 -delete

# Archive logs older than 7 days
find logs/detailed -name "backend_*.log" -mtime +7 -mtime -30 -exec \
  tar -czf logs/archive/backend_{}.tar.gz {} \; -delete

echo "Log cleanup complete"
```

---

## Monitoring Logs

### Watch for Errors
```bash
# Real-time error monitoring
tail -f logs/detailed/backend_*.log | grep --color=always "ERROR\|WARNING"

# Count errors per minute
watch -n 60 'grep "ERROR" logs/detailed/backend_*.log | tail -100 | wc -l'
```

### WebSocket Health
```bash
# Count active connections
grep "WS_CONNECT" logs/detailed/backend_*.log | wc -l
grep "WS_DISCONNECT" logs/detailed/backend_*.log | wc -l

# Find long-running sessions
grep "WS_CONNECT" logs/detailed/backend_*.log | \
  tail -20 | awk '{print $3, $7}'
```

---

## Summary

### Log Naming Convention
- Backend: `backend_{YYYYMMDD}_{HHMMSS}.log`
- Frontend: `frontend_{YYYYMMDD}_{HHMMSS}` (in localStorage)

### Quick Commands
```bash
# View latest backend log
tail -50 $(ls -t logs/detailed/backend_*.log | head -1)

# Watch latest backend log
tail -f $(ls -t logs/detailed/backend_*.log | head -1)

# Count today's errors
grep "ERROR" logs/detailed/backend_$(date +%Y%m%d)*.log | wc -l
```

### Browser Console Commands
```javascript
// View current frontend logs
logger.getLogs()

// Download logs
logger.downloadLogs()

// Clear logs
logger.clearLogs()

// Export as JSON
logger.exportLogs()
```

