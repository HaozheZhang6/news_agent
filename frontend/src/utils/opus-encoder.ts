/**
 * Opus Audio Encoder
 *
 * Provides Opus compression for audio using MediaRecorder API
 * Reduces file sizes by ~5x compared to WAV with minimal quality loss
 */

export interface OpusEncoderOptions {
  sampleRate?: number;
  bitrate?: number;
  mimeType?: string;
}

export class OpusEncoder {
  private sampleRate: number;
  private bitrate: number;
  private mimeType: string;

  constructor(options: OpusEncoderOptions = {}) {
    this.sampleRate = options.sampleRate || 16000;
    this.bitrate = options.bitrate || 64000; // 64 kbps default
    this.mimeType = this.selectMimeType(options.mimeType);
  }

  /**
   * Select best available MIME type for Opus encoding
   */
  private selectMimeType(preferred?: string): string {
    const types = [
      preferred,
      'audio/webm;codecs=opus',
      'audio/ogg;codecs=opus',
      'audio/webm',
    ].filter(Boolean) as string[];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        console.log(`✓ Using Opus MIME type: ${type}`);
        return type;
      }
    }

    // Fallback to any supported type
    console.warn('⚠️ Opus not supported, using default MediaRecorder codec');
    return '';
  }

  /**
   * Encode audio stream to Opus using MediaRecorder
   */
  async encodeStream(
    stream: MediaStream,
    onDataAvailable: (chunk: Blob) => void,
    timeslice: number = 1000
  ): Promise<MediaRecorder> {
    const options: MediaRecorderOptions = {};

    if (this.mimeType) {
      options.mimeType = this.mimeType;
    }

    // Set bitrate if supported
    if ('audioBitsPerSecond' in MediaRecorder.prototype) {
      options.audioBitsPerSecond = this.bitrate;
    }

    const recorder = new MediaRecorder(stream, options);

    recorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        onDataAvailable(event.data);
      }
    };

    recorder.start(timeslice);
    return recorder;
  }

  /**
   * Encode audio blob to Opus (if not already encoded)
   */
  async encodeBlob(audioBlob: Blob): Promise<Blob> {
    // If already Opus/WebM, return as is
    if (audioBlob.type.includes('opus') || audioBlob.type.includes('webm')) {
      return audioBlob;
    }

    // Otherwise, need to re-encode via MediaRecorder
    // This requires creating a temporary audio element and stream
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);

    try {
      // Create MediaStream from audio element
      const audioContext = new AudioContext({ sampleRate: this.sampleRate });
      const source = audioContext.createMediaElementSource(audio);
      const destination = audioContext.createMediaStreamDestination();
      source.connect(destination);

      // Encode stream
      const chunks: Blob[] = [];
      const recorder = await this.encodeStream(
        destination.stream,
        (chunk) => chunks.push(chunk),
        100
      );

      // Play audio to trigger encoding
      audio.play();

      // Wait for audio to finish
      await new Promise<void>((resolve) => {
        audio.onended = () => {
          recorder.stop();
          resolve();
        };
      });

      // Wait a bit for final chunks
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Combine chunks
      const opusBlob = new Blob(chunks, { type: this.mimeType });

      // Cleanup
      URL.revokeObjectURL(audioUrl);
      audioContext.close();

      return opusBlob;
    } catch (error) {
      URL.revokeObjectURL(audioUrl);
      throw error;
    }
  }

  /**
   * Get compression info
   */
  getConfig() {
    return {
      sampleRate: this.sampleRate,
      bitrate: this.bitrate,
      mimeType: this.mimeType,
      isSupported: MediaRecorder.isTypeSupported(this.mimeType),
    };
  }
}

/**
 * Opus Audio Recorder - Records directly to Opus format
 */
export class OpusAudioRecorder {
  private recorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: Blob[] = [];
  private isRecording: boolean = false;
  private opusEncoder: OpusEncoder;

  constructor(sampleRate: number = 16000, bitrate: number = 64000) {
    this.opusEncoder = new OpusEncoder({ sampleRate, bitrate });
  }

  /**
   * Start recording in Opus format
   */
  async start(stream: MediaStream): Promise<void> {
    if (this.isRecording) {
      console.warn('Already recording');
      return;
    }

    this.stream = stream;
    this.chunks = [];

    this.recorder = await this.opusEncoder.encodeStream(
      stream,
      (chunk) => {
        this.chunks.push(chunk);
      },
      100 // 100ms timeslices for streaming
    );

    this.isRecording = true;
    const config = this.opusEncoder.getConfig();
    console.log(`🎤 Opus recording started (${config.sampleRate}Hz, ${config.bitrate}bps)`);
  }

  /**
   * Stop recording and return Opus-encoded audio
   */
  stop(): Blob | null {
    if (!this.isRecording || !this.recorder) {
      console.warn('Not recording');
      return null;
    }

    this.isRecording = false;
    this.recorder.stop();

    if (this.chunks.length === 0) {
      console.warn('No audio data recorded');
      return null;
    }

    const mimeType = this.opusEncoder.getConfig().mimeType;
    const opusBlob = new Blob(this.chunks, { type: mimeType });

    console.log(`🎤 Opus recording stopped: ${opusBlob.size} bytes`);

    // Cleanup
    this.chunks = [];
    this.recorder = null;

    return opusBlob;
  }

  /**
   * Check if currently recording
   */
  isActive(): boolean {
    return this.isRecording;
  }

  /**
   * Get current recording duration (approximate)
   */
  getDuration(): number {
    // Estimate based on chunk count (100ms per chunk)
    return this.chunks.length * 0.1;
  }
}

/**
 * Utility functions
 */
export const OpusUtils = {
  /**
   * Check if Opus is supported
   */
  isSupported(): boolean {
    return (
      MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ||
      MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
    );
  },

  /**
   * Calculate compression ratio (WAV vs Opus)
   */
  getCompressionRatio(wavSize: number, opusSize: number): number {
    return wavSize / opusSize;
  },

  /**
   * Estimate Opus file size
   */
  estimateOpusSize(durationSeconds: number, bitrate: number = 64000): number {
    // Size = duration × bitrate / 8 (bits to bytes)
    return Math.ceil((durationSeconds * bitrate) / 8);
  },

  /**
   * Convert Blob to ArrayBuffer
   */
  async blobToArrayBuffer(blob: Blob): Promise<ArrayBuffer> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as ArrayBuffer);
      reader.onerror = reject;
      reader.readAsArrayBuffer(blob);
    });
  },
};
