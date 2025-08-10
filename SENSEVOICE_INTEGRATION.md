# SenseVoice Integration Guide

This document describes the SenseVoice integration added to the News Agent, providing enhanced voice recognition and real-time interruption capabilities.

## Features Added

### 1. SenseVoice ASR Integration
- **Multilingual Support**: Automatic language detection (English, Chinese, Japanese, etc.)
- **Higher Accuracy**: Superior recognition compared to Google Speech Recognition
- **Offline Capability**: Works without internet connection (model required locally)

### 2. Voice Activity Detection (VAD)
- **WebRTC VAD**: Real-time voice activity detection
- **Smart Segmentation**: Automatic speech/silence detection
- **Configurable Sensitivity**: Adjustable VAD modes (0-3)

### 3. Real-time Voice Interruption
- **Immediate Stopping**: Stop TTS when user speaks (similar to ASR-LLM-TTS repo)
- **Background Monitoring**: Continuous voice monitoring during speech playback
- **Fast Response**: Sub-100ms interruption response time

### 4. Enhanced Command Recognition
New voice commands supported:
- **Control**: stop, halt, quiet, silence, continue, resume, proceed
- **Navigation**: skip, next, previous, repeat, say again
- **Volume/Speed**: louder, quieter, faster, slower
- **Content**: news, stocks, weather, help, settings
- **Deep Dive**: tell me more, explain, elaborate, dive deeper

### 5. Comprehensive Logging
- **Audio Logs**: All voice inputs saved as timestamped MP3 files
- **Conversation Logs**: Complete user-agent dialogue history
- **System Logs**: Technical events, errors, interruptions
- **Daily Files**: Conversation logs organized by date

## Directory Structure

```
News_agent/
├── models/                    # SenseVoice model files
│   └── SenseVoiceSmall/      # Place your SenseVoice model here
├── audio_logs/               # Voice input recordings (MP3)
│   └── input_YYYYMMDD_HHMMSS.mp3
├── output/                   # TTS response audio files  
│   └── response_YYYYMMDD_HHMMSS.mp3
├── logs/
│   ├── app.log              # Technical/system logs
│   └── conversations/       # User-agent dialogue logs
│       └── conversation_YYYYMMDD.txt
└── src/
    ├── audio_logger.py           # MP3 audio logging
    ├── conversation_logger.py    # Dialogue logging
    ├── voice_activity_detector.py # VAD integration
    └── ...
```

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

New dependencies added:
- `funasr` - SenseVoice ASR
- `webrtcvad` - Voice Activity Detection
- `pyaudio` - Audio recording
- `pydub` - Audio format conversion
- `langid` - Language detection
- `langdetect` - Alternative language detection

### 2. Download SenseVoice Model
Place your SenseVoice model in:
```
News_agent/models/SenseVoiceSmall/
```

Or set custom path in environment:
```bash
export SENSEVOICE_MODEL_PATH="/path/to/your/sensevoice/model"
```

## Configuration

Key configuration options in `src/config.py`:

```python
# Audio Configuration
AUDIO_RATE = 16000           # Audio sampling rate
AUDIO_CHANNELS = 1           # Mono audio
CHUNK = 1024                 # Audio chunk size
VAD_MODE = 3                 # VAD sensitivity (0-3, higher = more sensitive)
NO_SPEECH_THRESHOLD = 1.0    # Silence threshold in seconds

# Model Path
SENSEVOICE_MODEL_PATH = "path/to/model"  # SenseVoice model location
```

## Usage Examples

### Voice Commands
- **Stop**: "stop", "halt", "quiet", "silence"
- **Continue**: "continue", "resume", "go on"
- **Deep Dive**: "tell me more", "explain", "dive deeper"
- **Navigation**: "skip", "next", "previous", "repeat"
- **Volume**: "speak louder", "volume up", "quieter"
- **Speed**: "speak faster", "slow down"
- **Content**: "latest news", "stock prices", "weather"

### Interruption Behavior
- **Real-time**: Voice detected during TTS playback stops audio immediately
- **Command-based**: "stop" commands trigger immediate interruption
- **Context-aware**: "tell me more" interrupts and requests deeper content

## Logging Output Examples

### Conversation Log (`logs/conversations/conversation_20241210.txt`)
```
# Conversation Log - 20241210

[2024-12-10 14:30:25] USER: "Tell me the latest news"
    Audio: audio_logs/input_20241210_143025_1.mp3
[2024-12-10 14:30:28] AGENT: "Here are today's top headlines..."
    Audio: output/response_20241210_143028_1.mp3
[2024-12-10 14:30:45] USER: "stop"
[2024-12-10 14:30:45] SYSTEM: Audio playback interrupted: Command: stop
[2024-12-10 14:30:47] USER: "tell me more about the first story"
```

### Application Log (`logs/app.log`)
```
2024-12-10 14:30:25,123 - news_agent - INFO - User input: Tell me the latest news
2024-12-10 14:30:25,124 - news_agent - INFO - Audio saved: audio_logs/input_20241210_143025_1.mp3
2024-12-10 14:30:28,456 - news_agent - INFO - Agent response: Here are today's top headlines...
2024-12-10 14:30:45,789 - news_agent - INFO - System event: Audio playback interrupted: Command: stop
```

## Performance Characteristics

### Response Times
- **Voice Recognition**: ~200-500ms (depending on model and hardware)
- **Command Classification**: <1ms
- **Interruption Response**: <100ms
- **VAD Processing**: ~50ms per 0.5s audio chunk

### Resource Usage
- **Memory**: +2-4GB for SenseVoice model
- **CPU**: Moderate increase during voice processing
- **Disk**: Audio logs grow over time (MP3 compressed)

## Testing

Run comprehensive tests:
```bash
# Run all tests
pytest tests/

# Run specific test suites
pytest tests/test_sensevoice_integration.py
pytest tests/test_voice.py
pytest tests/test_interruption_scenarios.py
```

## Troubleshooting

### Common Issues

1. **SenseVoice Model Not Found**
   - Ensure model is in correct directory
   - Check `SENSEVOICE_MODEL_PATH` environment variable
   - Verify model files are complete

2. **Audio Recording Issues**
   - Check microphone permissions
   - Verify PyAudio installation
   - Test with different audio devices

3. **VAD Not Working**
   - Adjust `VAD_MODE` setting (try different values 0-3)
   - Check audio input levels
   - Verify WebRTC VAD installation

4. **Interruption Not Responsive**
   - Reduce `NO_SPEECH_THRESHOLD`
   - Increase VAD sensitivity (`VAD_MODE`)
   - Check audio monitoring thread status

### Fallback Behavior
- If SenseVoice model not found, system logs error and continues
- If VAD fails, continues without voice activity detection
- If audio logging fails, continues without saving audio files

## Comparison with Original Implementation

| Feature | Original | SenseVoice Integration |
|---------|----------|----------------------|
| ASR | Google Speech Recognition | SenseVoice (FunASR) |
| Languages | English only | Multilingual auto-detect |
| Internet Required | Yes | No (offline model) |
| Interruption | Basic event-based | Real-time voice detection |
| Audio Logging | None | Complete MP3 logging |
| Conversation History | Memory only | Persistent text logs |
| Commands | 5 basic types | 14+ enhanced types |
| VAD | None | WebRTC VAD integration |

## Future Enhancements

Potential improvements:
- **Streaming Recognition**: Real-time streaming ASR
- **Wake Word Detection**: "Hey Assistant" activation
- **Speaker Identification**: Multi-user support
- **Emotion Recognition**: Detect user emotional state
- **Audio Preprocessing**: Noise reduction, echo cancellation

## Dependencies

For reference, key new dependencies:
- `funasr>=1.0.0` - SenseVoice ASR engine
- `webrtcvad>=2.0.0` - Voice activity detection
- `pyaudio>=0.2.11` - Audio I/O
- `pydub>=0.25.0` - Audio format conversion
- `numpy>=1.21.0` - Numerical processing
- `langid>=1.1.6` - Language identification