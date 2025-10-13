/**
 * WAV Audio Encoder
 *
 * Encodes raw PCM audio data to WAV format for reliable backend processing.
 * WAV files are simple: header + PCM data, always valid, no compression needed.
 */

export interface WAVEncoderOptions {
  sampleRate?: number;
  numChannels?: number;
  bitDepth?: number;
}

export class WAVEncoder {
  private sampleRate: number;
  private numChannels: number;
  private bitDepth: number;

  constructor(options: WAVEncoderOptions = {}) {
    this.sampleRate = options.sampleRate || 16000; // Match backend expectation
    this.numChannels = options.numChannels || 1; // Mono
    this.bitDepth = options.bitDepth || 16; // 16-bit PCM
  }

  /**
   * Encode Float32Array PCM samples to WAV format
   */
  encodeFromFloat32(samples: Float32Array): ArrayBuffer {
    const bytesPerSample = this.bitDepth / 8;
    const blockAlign = this.numChannels * bytesPerSample;
    const byteRate = this.sampleRate * blockAlign;
    const dataSize = samples.length * bytesPerSample;
    const buffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(buffer);

    // Write WAV header
    this.writeString(view, 0, 'RIFF'); // ChunkID
    view.setUint32(4, 36 + dataSize, true); // ChunkSize
    this.writeString(view, 8, 'WAVE'); // Format

    // Write fmt subchunk
    this.writeString(view, 12, 'fmt '); // Subchunk1ID
    view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
    view.setUint16(20, 1, true); // AudioFormat (1 for PCM)
    view.setUint16(22, this.numChannels, true); // NumChannels
    view.setUint32(24, this.sampleRate, true); // SampleRate
    view.setUint32(28, byteRate, true); // ByteRate
    view.setUint16(32, blockAlign, true); // BlockAlign
    view.setUint16(34, this.bitDepth, true); // BitsPerSample

    // Write data subchunk
    this.writeString(view, 36, 'data'); // Subchunk2ID
    view.setUint32(40, dataSize, true); // Subchunk2Size

    // Convert float samples to 16-bit PCM
    this.floatTo16BitPCM(view, 44, samples);

    return buffer;
  }

  /**
   * Encode from AudioBuffer (Web Audio API)
   */
  encodeFromAudioBuffer(audioBuffer: AudioBuffer): ArrayBuffer {
    // Get channel data (use first channel for mono)
    const samples = audioBuffer.getChannelData(0);
    return this.encodeFromFloat32(samples);
  }

  /**
   * Convert Float32Array samples (-1.0 to 1.0) to 16-bit PCM
   */
  private floatTo16BitPCM(view: DataView, offset: number, samples: Float32Array): void {
    for (let i = 0; i < samples.length; i++) {
      // Clamp to [-1, 1]
      const sample = Math.max(-1, Math.min(1, samples[i]));
      // Convert to 16-bit integer
      const int16 = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
      view.setInt16(offset + i * 2, int16, true);
    }
  }

  /**
   * Write ASCII string to DataView
   */
  private writeString(view: DataView, offset: number, str: string): void {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  }

  /**
   * Get current configuration
   */
  getConfig() {
    return {
      sampleRate: this.sampleRate,
      numChannels: this.numChannels,
      bitDepth: this.bitDepth
    };
  }
}

/**
 * PCM Audio Recorder using Web Audio API
 *
 * Captures raw PCM data from microphone using AudioWorkletNode or ScriptProcessorNode
 */
export class PCMAudioRecorder {
  private audioContext: AudioContext | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private stream: MediaStream | null = null;
  private pcmChunks: Float32Array[] = [];
  private isRecording: boolean = false;
  private wavEncoder: WAVEncoder;

  constructor(sampleRate: number = 16000) {
    this.wavEncoder = new WAVEncoder({ sampleRate });
  }

  /**
   * Start recording audio from microphone
   */
  async start(stream: MediaStream): Promise<void> {
    if (this.isRecording) {
      console.warn('Already recording');
      return;
    }

    this.stream = stream;
    this.pcmChunks = [];

    // Create audio context with target sample rate
    this.audioContext = new AudioContext({ sampleRate: 16000 });
    this.sourceNode = this.audioContext.createMediaStreamSource(stream);

    // Use ScriptProcessorNode for PCM capture
    // Note: ScriptProcessorNode is deprecated but widely supported
    // AudioWorkletNode is the modern alternative but requires more setup
    const bufferSize = 4096; // Process in 4KB chunks
    this.processorNode = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

    this.processorNode.onaudioprocess = (event) => {
      if (!this.isRecording) return;

      // Get PCM data from input buffer
      const inputData = event.inputBuffer.getChannelData(0);

      // Copy to new array (inputData is reused by Web Audio API)
      const pcmData = new Float32Array(inputData.length);
      pcmData.set(inputData);

      this.pcmChunks.push(pcmData);
    };

    // Connect nodes
    this.sourceNode.connect(this.processorNode);
    this.processorNode.connect(this.audioContext.destination);

    this.isRecording = true;
    console.log('🎤 PCM recording started (16kHz, mono, 16-bit)');
  }

  /**
   * Stop recording and return WAV-encoded audio
   */
  stop(): ArrayBuffer | null {
    if (!this.isRecording) {
      console.warn('Not recording');
      return null;
    }

    this.isRecording = false;

    // Disconnect nodes
    if (this.processorNode && this.sourceNode) {
      this.sourceNode.disconnect(this.processorNode);
      this.processorNode.disconnect(this.audioContext!.destination);
    }

    // Close audio context
    if (this.audioContext) {
      this.audioContext.close();
    }

    // Combine all PCM chunks
    if (this.pcmChunks.length === 0) {
      console.warn('No audio data recorded');
      return null;
    }

    const totalLength = this.pcmChunks.reduce((acc, chunk) => acc + chunk.length, 0);
    const combinedPCM = new Float32Array(totalLength);

    let offset = 0;
    for (const chunk of this.pcmChunks) {
      combinedPCM.set(chunk, offset);
      offset += chunk.length;
    }

    console.log(`🎤 PCM recording stopped: ${combinedPCM.length} samples (${(combinedPCM.length / 16000).toFixed(2)}s)`);

    // Encode to WAV
    const wavData = this.wavEncoder.encodeFromFloat32(combinedPCM);
    console.log(`📦 Encoded to WAV: ${wavData.byteLength} bytes`);

    // Cleanup
    this.pcmChunks = [];
    this.audioContext = null;
    this.sourceNode = null;
    this.processorNode = null;

    return wavData;
  }

  /**
   * Check if currently recording
   */
  isActive(): boolean {
    return this.isRecording;
  }

  /**
   * Get current recording duration in seconds
   */
  getDuration(): number {
    const totalSamples = this.pcmChunks.reduce((acc, chunk) => acc + chunk.length, 0);
    return totalSamples / 16000;
  }
}

/**
 * Utility functions
 */
export const WAVUtils = {
  /**
   * Validate WAV file header
   */
  isValidWAV(buffer: ArrayBuffer): boolean {
    if (buffer.byteLength < 44) return false;

    const view = new DataView(buffer);
    const riff = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3));
    const wave = String.fromCharCode(view.getUint8(8), view.getUint8(9), view.getUint8(10), view.getUint8(11));

    return riff === 'RIFF' && wave === 'WAVE';
  },

  /**
   * Get WAV file info
   */
  getWAVInfo(buffer: ArrayBuffer): { sampleRate: number; numChannels: number; bitDepth: number; duration: number } | null {
    if (!WAVUtils.isValidWAV(buffer)) return null;

    const view = new DataView(buffer);
    const numChannels = view.getUint16(22, true);
    const sampleRate = view.getUint32(24, true);
    const bitDepth = view.getUint16(34, true);
    const dataSize = view.getUint32(40, true);
    const numSamples = dataSize / (numChannels * (bitDepth / 8));
    const duration = numSamples / sampleRate;

    return { sampleRate, numChannels, bitDepth, duration };
  },

  /**
   * Convert ArrayBuffer to Blob
   */
  toBlob(buffer: ArrayBuffer): Blob {
    return new Blob([buffer], { type: 'audio/wav' });
  },

  /**
   * Convert ArrayBuffer to base64
   */
  toBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }
};
