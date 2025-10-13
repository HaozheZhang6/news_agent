/**
 * Audio Base64 Encoder Utility
 * 
 * Provides utilities for encoding audio data to base64 format suitable for WebSocket transmission.
 * Used by microphone capture and file upload components.
 */

export interface AudioEncodingOptions {
  /** Audio format (webm, wav, mp3, etc.) */
  format: string;
  /** Sample rate in Hz */
  sampleRate?: number;
  /** Whether this is the final chunk */
  isFinal?: boolean;
  /** Session ID for WebSocket messages */
  sessionId?: string;
  /** User ID */
  userId?: string;
  /** Enable compression (default: true) */
  compress?: boolean;
  /** Compression codec (opus, aac, mp3) */
  codec?: 'opus' | 'aac' | 'mp3' | 'webm';
  /** Compression bitrate */
  bitrate?: number;
  /** Original filename (for file uploads) */
  originalFilename?: string;
}

export interface EncodedAudioMessage {
  event: 'audio_chunk';
  data: {
    audio_chunk: string;
    format: string;
    is_final: boolean;
    session_id: string;
    user_id: string;
    sample_rate?: number;
    file_size?: number;
    original_filename?: string;
    encoded_at?: string;
  };
}

export class AudioBase64Encoder {
  private defaultUserId: string;
  private defaultSessionId: string;
  private compressionCodecs: Record<string, any>;

  constructor(defaultUserId: string = '03f6b167-0c4d-4983-a380-54b8eb42f830') {
    this.defaultUserId = defaultUserId;
    this.defaultSessionId = this.generateSessionId();
    
    // Compression codec configurations
    this.compressionCodecs = {
      opus: {
        mimeType: 'audio/webm;codecs=opus',
        bitrate: 64000,
        description: 'Opus - Best for real-time speech (WebRTC standard)'
      },
      webm: {
        mimeType: 'audio/webm;codecs=opus',
        bitrate: 64000,
        description: 'WebM - Web optimized'
      },
      mp3: {
        mimeType: 'audio/mpeg',
        bitrate: 128000,
        description: 'MP3 - Widely supported'
      },
      aac: {
        mimeType: 'audio/mp4;codecs=mp4a.40.2',
        bitrate: 128000,
        description: 'AAC - High quality compression'
      }
    };
  }

  /**
   * Generate a unique session ID
   */
  private generateSessionId(): string {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  /**
   * Compress audio blob using Web Audio API
   */
  private async compressAudioBlob(
    audioBlob: Blob, 
    codec: string = 'opus'
  ): Promise<{ compressedBlob: Blob; compressionInfo: any }> {
    const codecConfig = this.compressionCodecs[codec];
    if (!codecConfig) {
      throw new Error(`Unsupported codec: ${codec}`);
    }

    // Check if the codec is supported
    if (!MediaRecorder.isTypeSupported(codecConfig.mimeType)) {
      console.warn(`Codec ${codec} not supported, falling back to webm`);
      return {
        compressedBlob: audioBlob,
        compressionInfo: { codec: 'webm', fallback: true }
      };
    }

    try {
      // Since we already have the audio as WebM/Opus from MediaRecorder,
      // we don't need to re-encode it. Just return the original blob.
      // The browser's MediaRecorder already compressed it with Opus codec.
      return {
        compressedBlob: audioBlob,
        compressionInfo: {
          codec,
          original_size: audioBlob.size,
          compressed_size: audioBlob.size,
          compression_ratio: 1.0,
          bitrate: codecConfig.bitrate,
          mimeType: codecConfig.mimeType,
          note: 'Already compressed by MediaRecorder'
        }
      };
    } catch (error) {
      console.warn(`Compression failed: ${error}, using original`);
      return {
        compressedBlob: audioBlob,
        compressionInfo: { codec: 'original', fallback: true }
      };
    }
  }

  /**
   * Encode Blob (from MediaRecorder) to base64 WebSocket message with compression
   */
  async encodeBlob(
    audioBlob: Blob, 
    options: Partial<AudioEncodingOptions> = {}
  ): Promise<EncodedAudioMessage> {
    const compress = options.compress ?? true;
    const codec = options.codec || 'opus';
    
    let finalBlob = audioBlob;
    let compressionInfo = null;

    // Compress audio if requested
    if (compress) {
      try {
        const { compressedBlob, compressionInfo: compInfo } = await this.compressAudioBlob(audioBlob, codec);
        finalBlob = compressedBlob;
        compressionInfo = compInfo;
        
        if (compInfo.compression_ratio) {
          console.log(`🎵 Compressed with ${codec.toUpperCase()}: ${compInfo.compression_ratio.toFixed(1)}x smaller`);
        }
      } catch (error) {
        console.warn(`⚠️ Compression failed, using original: ${error}`);
      }
    }

    const base64Audio = await this.blobToBase64(finalBlob);
    
    return {
      event: 'audio_chunk',
      data: {
        audio_chunk: base64Audio,
        format: options.format || (compressionInfo?.mimeType ? this.getFormatFromMimeType(compressionInfo.mimeType) : 'webm'),
        is_final: options.isFinal ?? true,
        session_id: options.sessionId || this.defaultSessionId,
        user_id: options.userId || this.defaultUserId,
        sample_rate: options.sampleRate || 48000,
        file_size: finalBlob.size,
        original_filename: options.originalFilename,
        encoded_at: new Date().toISOString(),
        compression: compressionInfo
      }
    };
  }

  /**
   * Encode File (from file input) to base64 WebSocket message
   */
  async encodeFile(
    audioFile: File, 
    options: Partial<AudioEncodingOptions> = {}
  ): Promise<EncodedAudioMessage> {
    const base64Audio = await this.fileToBase64(audioFile);
    const format = this.getFileFormat(audioFile.name) || options.format || 'wav';
    
    return {
      event: 'audio_chunk',
      data: {
        audio_chunk: base64Audio,
        format,
        is_final: options.isFinal ?? true,
        session_id: options.sessionId || this.defaultSessionId,
        user_id: options.userId || this.defaultUserId,
        sample_rate: options.sampleRate || this.getDefaultSampleRate(format),
        file_size: audioFile.size,
        original_filename: audioFile.name,
        encoded_at: new Date().toISOString()
      }
    };
  }

  /**
   * Encode ArrayBuffer to base64 WebSocket message
   */
  encodeArrayBuffer(
    audioBuffer: ArrayBuffer, 
    options: Partial<AudioEncodingOptions> = {}
  ): EncodedAudioMessage {
    const base64Audio = this.arrayBufferToBase64(audioBuffer);
    
    return {
      event: 'audio_chunk',
      data: {
        audio_chunk: base64Audio,
        format: options.format || 'wav',
        is_final: options.isFinal ?? true,
        session_id: options.sessionId || this.defaultSessionId,
        user_id: options.userId || this.defaultUserId,
        sample_rate: options.sampleRate || 16000,
        file_size: audioBuffer.byteLength,
        encoded_at: new Date().toISOString()
      }
    };
  }

  /**
   * Convert Blob to base64 string
   */
  private async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        // Remove data URL prefix (e.g., "data:audio/webm;base64,")
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Convert File to base64 string
   */
  private async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Convert ArrayBuffer to base64 string
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Get file format from filename
   */
  private getFileFormat(filename: string): string | null {
    const ext = filename.toLowerCase().split('.').pop();
    const formatMap: Record<string, string> = {
      'wav': 'wav',
      'webm': 'webm',
      'mp3': 'mp3',
      'm4a': 'm4a',
      'ogg': 'ogg',
      'flac': 'flac'
    };
    return formatMap[ext || ''] || null;
  }

  /**
   * Get format from MIME type
   */
  private getFormatFromMimeType(mimeType: string): string {
    const mimeToFormat: Record<string, string> = {
      'audio/webm;codecs=opus': 'webm',
      'audio/mpeg': 'mp3',
      'audio/mp4;codecs=mp4a.40.2': 'm4a',
      'audio/ogg': 'ogg',
      'audio/wav': 'wav'
    };
    return mimeToFormat[mimeType] || 'webm';
  }

  /**
   * Get default sample rate for format
   */
  private getDefaultSampleRate(format: string): number {
    const sampleRates: Record<string, number> = {
      'wav': 16000,
      'webm': 48000,
      'mp3': 44100,
      'm4a': 44100,
      'ogg': 48000,
      'flac': 44100
    };
    return sampleRates[format] || 16000;
  }

  /**
   * Create a new session ID
   */
  newSession(): string {
    this.defaultSessionId = this.generateSessionId();
    return this.defaultSessionId;
  }

  /**
   * Get current session ID
   */
  getCurrentSessionId(): string {
    return this.defaultSessionId;
  }

  /**
   * Set user ID
   */
  setUserId(userId: string): void {
    this.defaultUserId = userId;
  }

  /**
   * Get current user ID
   */
  getCurrentUserId(): string {
    return this.defaultUserId;
  }
}

/**
 * Utility functions for audio encoding
 */
export const AudioUtils = {
  /**
   * Check if file is a supported audio format
   */
  isSupportedAudioFile(file: File): boolean {
    const supportedTypes = [
      'audio/wav',
      'audio/webm',
      'audio/mp3',
      'audio/mpeg',
      'audio/m4a',
      'audio/ogg',
      'audio/flac'
    ];
    
    const supportedExtensions = ['.wav', '.webm', '.mp3', '.m4a', '.ogg', '.flac'];
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
    
    return supportedTypes.includes(file.type) || supportedExtensions.includes(fileExt);
  },

  /**
   * Get file size in human readable format
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  /**
   * Get encoding compression ratio
   */
  getCompressionRatio(originalSize: number, encodedSize: number): number {
    return encodedSize / originalSize;
  },

  /**
   * Validate audio file size (max 10MB)
   */
  validateFileSize(file: File, maxSizeMB: number = 10): boolean {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    return file.size <= maxSizeBytes;
  }
};

/**
 * Default encoder instance
 */
export const defaultAudioEncoder = new AudioBase64Encoder();

/**
 * React hook for audio encoding
 */
export function useAudioEncoder(userId?: string) {
  const encoder = new AudioBase64Encoder(userId);
  
  return {
    encodeBlob: encoder.encodeBlob.bind(encoder),
    encodeFile: encoder.encodeFile.bind(encoder),
    encodeArrayBuffer: encoder.encodeArrayBuffer.bind(encoder),
    newSession: encoder.newSession.bind(encoder),
    getCurrentSessionId: encoder.getCurrentSessionId.bind(encoder),
    setUserId: encoder.setUserId.bind(encoder),
    getCurrentUserId: encoder.getCurrentUserId.bind(encoder)
  };
}
