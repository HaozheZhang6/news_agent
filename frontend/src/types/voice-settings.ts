/**
 * Voice Settings Types
 *
 * Matches backend VoiceSettings model for configuration
 */

export interface VoiceSettings {
  // Speech Settings
  speech_rate: number;
  voice_type: string;
  interruption_sensitivity: number;
  auto_play: boolean;
  noise_reduction: boolean;
  echo_cancellation: boolean;

  // VAD Configuration
  voice_activity_detection: boolean;
  vad_threshold: number;              // 0.01-0.1
  silence_timeout_ms: number;         // 300-2000ms
  min_recording_duration_ms: number;  // 300-2000ms
  vad_check_interval_ms: number;      // 100-500ms

  // Backend VAD Validation
  backend_vad_enabled: boolean;
  backend_vad_mode: number;           // 0-3 (WebRTC VAD aggressiveness)
  backend_energy_threshold: number;

  // Audio Compression
  use_compression: boolean;
  compression_codec: 'opus' | 'webm';
  compression_bitrate: number;
}

export const DEFAULT_VOICE_SETTINGS: VoiceSettings = {
  // Speech Settings
  speech_rate: 1.0,
  voice_type: 'en-US-AriaNeural',
  interruption_sensitivity: 0.5,
  auto_play: true,
  noise_reduction: true,
  echo_cancellation: true,

  // VAD Configuration
  voice_activity_detection: true,
  vad_threshold: 0.02,
  silence_timeout_ms: 700,
  min_recording_duration_ms: 500,
  vad_check_interval_ms: 250,

  // Backend VAD Validation
  backend_vad_enabled: true,
  backend_vad_mode: 3,
  backend_energy_threshold: 500.0,

  // Audio Compression
  use_compression: false,
  compression_codec: 'opus',
  compression_bitrate: 64000,
};

/**
 * VAD Configuration Presets
 */
export const VAD_PRESETS = {
  // Very sensitive - picks up soft speech, may detect noise
  sensitive: {
    vad_threshold: 0.01,
    silence_timeout_ms: 500,
    backend_vad_mode: 0,
    backend_energy_threshold: 200.0,
  },

  // Balanced - good for most environments
  balanced: {
    vad_threshold: 0.02,
    silence_timeout_ms: 700,
    backend_vad_mode: 2,
    backend_energy_threshold: 500.0,
  },

  // Strict - filters noise, requires clear speech
  strict: {
    vad_threshold: 0.05,
    silence_timeout_ms: 1500,
    backend_vad_mode: 3,
    backend_energy_threshold: 800.0,
  },
} as const;

/**
 * Audio Format Options
 */
export interface AudioFormatConfig {
  format: 'wav' | 'opus' | 'webm';
  sample_rate: number;
  use_compression: boolean;
  compression_bitrate?: number;
}

export const AUDIO_FORMAT_PRESETS: Record<string, AudioFormatConfig> = {
  // Uncompressed WAV - highest quality, largest size
  uncompressed: {
    format: 'wav',
    sample_rate: 16000,
    use_compression: false,
  },

  // Opus compressed - best for real-time, 5x smaller
  compressed: {
    format: 'opus',
    sample_rate: 16000,
    use_compression: true,
    compression_bitrate: 64000,
  },

  // High quality compressed - better quality, 3x smaller
  high_quality: {
    format: 'opus',
    sample_rate: 16000,
    use_compression: true,
    compression_bitrate: 128000,
  },
};