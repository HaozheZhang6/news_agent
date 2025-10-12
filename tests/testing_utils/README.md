# Testing Utilities

Utilities for testing the Voice News Agent audio pipeline.

## Contents

- **voice_encoder.py** - Compress and encode audio files for WebSocket transmission
- **AUDIO_TESTING_GUIDE.md** - Comprehensive guide for audio testing pipeline

## Quick Start

### Compress a single voice sample:

```bash
python voice_encoder.py \
  ../../voice_samples/test_price_nvda_today.wav \
  -o ../../voice_samples/encoded_compressed_opus/test_price_nvda_today_compressed_opus.json \
  --codec opus
```

### Batch compress all samples:

```bash
python voice_encoder.py --batch ../../voice_samples/ --codec opus
```

### Test compression without saving:

```bash
python voice_encoder.py --test ../../voice_samples/test_price_nvda_today.wav --codec opus
```

## Documentation

See [AUDIO_TESTING_GUIDE.md](./AUDIO_TESTING_GUIDE.md) for:
- Complete audio pipeline documentation
- Voice sample generation guide
- Testing procedures
- Session validation
- Traceability and debugging

## Related Test Scripts

- `../../test_websocket_simple.py` - Basic WebSocket test
- `../../test_compressed_audio.py` - Compression analysis
- `../../test_comprehensive_opus.py` - Multi-query session validation
