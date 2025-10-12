/**
 * Frontend logger for Voice News Agent
 * Logs to console with timestamps and categories
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: any;
}

class VoiceAgentLogger {
  private logs: LogEntry[] = [];
  private maxLogs = 1000;
  private enableConsole = true;
  private enableStorage = true;

  private log(level: LogLevel, category: string, message: string, data?: any) {
    const timestamp = new Date().toISOString();
    const entry: LogEntry = { timestamp, level, category, message, data };
    
    // Store in memory
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Console output
    if (this.enableConsole) {
      const emoji = this.getEmoji(category);
      const color = this.getColor(level);
      const logFn = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
      
      logFn(
        `%c${emoji} ${category.toUpperCase()} | ${message}`,
        `color: ${color}; font-weight: ${level === 'error' ? 'bold' : 'normal'}`,
        data || ''
      );
    }

    // LocalStorage (for debugging) - use frontend_{date}_{time} format
    if (this.enableStorage) {
      try {
        // Get or create session timestamp
        if (!localStorage.getItem('frontend_log_session')) {
          const now = new Date();
          const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`;
          localStorage.setItem('frontend_log_session', timestamp);
        }
        
        const sessionTimestamp = localStorage.getItem('frontend_log_session');
        const storageKey = `frontend_${sessionTimestamp}`;
        const existingLogs = localStorage.getItem(storageKey);
        const logsArray = existingLogs ? JSON.parse(existingLogs) : [];
        logsArray.push(entry);
        
        // Keep only last 500 logs in localStorage
        if (logsArray.length > 500) {
          logsArray.shift();
        }
        
        localStorage.setItem(storageKey, JSON.stringify(logsArray));
      } catch (e) {
        // Ignore storage errors
      }
    }
  }

  private getEmoji(category: string): string {
    const emojiMap: Record<string, string> = {
      'ws': '🔌',
      'audio': '🎤',
      'vad': '📊',
      'playback': '🔊',
      'transcription': '📝',
      'response': '🤖',
      'interrupt': '🛑',
      'error': '❌',
      'warning': '⚠️',
      'info': 'ℹ️',
      'debug': '🔍'
    };
    return emojiMap[category.toLowerCase()] || '📌';
  }

  private getColor(level: LogLevel): string {
    const colorMap: Record<LogLevel, string> = {
      debug: '#666',
      info: '#0066cc',
      warn: '#ff9900',
      error: '#cc0000'
    };
    return colorMap[level];
  }

  // WebSocket logs
  wsConnect(url: string) {
    this.log('info', 'ws', `Connecting to ${url}`);
  }

  wsConnected(sessionId: string) {
    this.log('info', 'ws', `Connected | session=${sessionId.slice(0, 8)}...`);
  }

  wsDisconnect(reason?: string) {
    this.log('info', 'ws', `Disconnected${reason ? ` | reason=${reason}` : ''}`);
  }

  wsMessageSent(event: string, sessionId?: string) {
    this.log('debug', 'ws', `📤 SEND | event=${event}${sessionId ? ` | session=${sessionId.slice(0, 8)}...` : ''}`);
  }

  wsMessageReceived(event: string, sessionId?: string) {
    this.log('debug', 'ws', `📥 RECV | event=${event}${sessionId ? ` | session=${sessionId.slice(0, 8)}...` : ''}`);
  }

  wsError(error: any) {
    this.log('error', 'ws', `WebSocket error`, error);
  }

  // Audio logs
  audioRecordingStart() {
    this.log('info', 'audio', 'Recording started with VAD');
  }

  audioRecordingStop() {
    this.log('info', 'audio', 'Recording stopped');
  }

  audioChunkSent(sizeBytes: number, sessionId?: string) {
    this.log('debug', 'audio', `📤 SEND | size=${sizeBytes} bytes${sessionId ? ` | session=${sessionId.slice(0, 8)}...` : ''}`);
  }

  audioChunkReceived(chunkIndex: number, sessionId?: string) {
    this.log('debug', 'audio', `📥 RECV | chunk=${chunkIndex}${sessionId ? ` | session=${sessionId.slice(0, 8)}...` : ''}`);
  }

  // VAD logs
  vadSpeechDetected() {
    this.log('debug', 'vad', 'Speech detected');
  }

  vadSilenceDetected(duration: number) {
    this.log('debug', 'vad', `Silence detected | duration=${duration}ms`);
  }

  vadSendTriggered() {
    this.log('info', 'vad', 'Silence threshold reached → sending audio');
  }

  // Playback logs
  playbackStart() {
    this.log('info', 'playback', 'TTS playback started');
  }

  playbackStop() {
    this.log('info', 'playback', 'TTS playback stopped');
  }

  playbackInterrupted() {
    this.log('info', 'playback', '🛑 Playback interrupted by user speech');
  }

  // Transcription & Response logs
  transcriptionReceived(text: string) {
    this.log('info', 'transcription', `"${text.slice(0, 50)}${text.length > 50 ? '...' : ''}"`);
  }

  responseReceived(text: string) {
    this.log('info', 'response', `"${text.slice(0, 50)}${text.length > 50 ? '...' : ''}"`);
  }

  // Interruption logs
  interruptSent(reason: string) {
    this.log('info', 'interrupt', `Interrupt signal sent | reason=${reason}`);
  }

  // Error logs
  error(category: string, message: string, error?: any) {
    this.log('error', category, message, error);
  }

  warn(category: string, message: string, data?: any) {
    this.log('warn', category, message, data);
  }

  info(category: string, message: string, data?: any) {
    this.log('info', category, message, data);
  }

  debug(category: string, message: string, data?: any) {
    this.log('debug', category, message, data);
  }

  // Utility methods
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clearLogs() {
    this.logs = [];
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  downloadLogs() {
    const sessionTimestamp = localStorage.getItem('frontend_log_session') || 'unknown';
    const blob = new Blob([this.exportLogs()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `frontend_${sessionTimestamp}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// Global logger instance
export const logger = new VoiceAgentLogger();

