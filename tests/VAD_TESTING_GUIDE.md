# VAD and Interruption Testing Framework

Comprehensive automated testing framework for Voice Activity Detection (VAD) and interruption handling in the News Agent voice interface.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Quick Start](#quick-start)
- [Test Suites](#test-suites)
- [Running Tests](#running-tests)
- [Adding New Tests](#adding-new-tests)
- [Troubleshooting](#troubleshooting)

## Overview

This testing framework provides automated validation for:

1. **Backend VAD Validation** - Energy-based and WebRTC VAD testing
2. **Interruption Flow** - User interruption handling during agent speech
3. **End-to-End Integration** - Complete voice interaction flow

### Why This Framework?

- **Automated Testing**: No manual testing needed for VAD and interruption features
- **Real Audio Samples**: Uses actual voice recordings from `tests/voice_samples/`
- **Performance Metrics**: Measures latency and processing times
- **Regression Prevention**: Catches VAD threshold changes and interruption bugs

## Test Structure

```
tests/
├── voice_samples/
│   └── wav/                    # Test audio samples (WAV format)
│       ├── test_price_aapl.wav
│       ├── test_news_nvda_latest.wav
│       └── ...
├── backend/local/core/
│   ├── test_vad_validation.py         # VAD validation tests
│   └── test_interruption_flow.py      # Interruption handling tests
├── integration/
│   └── test_e2e_vad_interruption.py   # End-to-end integration tests
├── run_vad_tests.py                    # Main test runner
└── VAD_TESTING_GUIDE.md               # This guide
```

## Quick Start

### Prerequisites

```bash
# Install test dependencies
uv pip install pytest pytest-asyncio pytest-html numpy webrtcvad

# Verify audio samples exist
ls tests/voice_samples/wav/
```

### Run All Tests

```bash
# From project root
python tests/run_vad_tests.py
```

### Run Quick Tests

```bash
# Run quick subset for CI/CD
python tests/run_vad_tests.py --quick
```

### Run Specific Test Suite

```bash
# Only VAD validation tests
python tests/run_vad_tests.py --vad-only

# Only interruption tests
python tests/run_vad_tests.py --interruption-only

# Only end-to-end tests
python tests/run_vad_tests.py --e2e-only
```

### Generate HTML Report

```bash
# Creates reports/vad_tests.html
python tests/run_vad_tests.py --html
```

## Test Suites

### 1. VAD Validation Tests (`test_vad_validation.py`)

Tests the backend audio validation system.

#### Test Classes

**TestVADValidation**
- `test_audio_samples_exist` - Verifies test audio samples are available
- `test_energy_calculation` - Tests RMS energy calculation for all samples
- `test_webrtc_vad_validation` - Tests WebRTC VAD speech detection
- `test_full_validation_pipeline` - Tests complete validation (energy + WebRTC)
- `test_speech_ratio_threshold_15_percent` - Validates 15% threshold is working
- `test_lenient_vs_strict_validation` - Compares validation modes
- `test_specific_samples` - Parametrized tests for specific samples

**TestVADEdgeCases**
- `test_empty_audio` - Empty audio handling
- `test_invalid_sample_rate` - Invalid sample rate handling
- `test_corrupted_audio` - Corrupted audio handling
- `test_very_short_audio` - Short audio handling

**TestVADPerformance**
- `test_validation_speed` - Measures validation latency

#### Example Usage

```bash
# Run all VAD tests with verbose output
pytest tests/backend/local/core/test_vad_validation.py -v -s

# Run specific test
pytest tests/backend/local/core/test_vad_validation.py::TestVADValidation::test_speech_ratio_threshold_15_percent -v

# Run with HTML report
pytest tests/backend/local/core/test_vad_validation.py --html=reports/vad.html
```

#### Example Output

```
test_audio_samples_exist PASSED
✓ Found 30 audio samples

test_energy_calculation PASSED
  test_price_aapl: energy=1234.5 (threshold=500.0)
  test_news_nvda: energy=987.3 (threshold=500.0)
✓ 28/30 samples passed energy threshold

test_webrtc_vad_validation PASSED
  ✓ test_price_aapl: speech_ratio=0.45
  ✓ test_news_nvda: speech_ratio=0.38
✓ 26/30 samples detected as speech

test_speech_ratio_threshold_15_percent PASSED
  ✓ test_followup_2: speech_ratio=0.22 (would have been rejected with 30% threshold)
✓ Found 5 samples with 15-30% speech ratio
```

### 2. Interruption Flow Tests (`test_interruption_flow.py`)

Tests user interruption handling during agent responses.

#### Test Classes

**TestInterruptionFlow**
- `test_interrupt_signal_handling` - Verifies interrupt signal processing
- `test_streaming_interruption` - Tests TTS streaming stops on interrupt
- `test_multiple_interruptions` - Tests handling multiple interrupts
- `test_audio_chunk_processing_with_interruption` - Tests audio during interrupt
- `test_session_cleanup_on_disconnect` - Tests cleanup on disconnect

**TestInterruptionTiming**
- `test_interrupt_latency` - Measures interrupt handling latency
- `test_streaming_stop_latency` - Measures streaming stop latency

**TestInterruptionScenarios**
- `test_interrupt_during_first_tts_chunk` - Early interruption
- `test_rapid_audio_chunks_with_interrupts` - Rapid interruptions

#### Example Usage

```bash
# Run all interruption tests
pytest tests/backend/local/core/test_interruption_flow.py -v -s

# Run specific scenario
pytest tests/backend/local/core/test_interruption_flow.py::TestInterruptionScenarios::test_rapid_audio_chunks_with_interrupts -v
```

#### Example Output

```
test_interrupt_signal_handling PASSED
✓ Interrupt flag set for session 245c7d2c...
✓ Interrupt confirmation sent

test_streaming_interruption PASSED
✓ TTS streaming interrupted successfully

test_interrupt_latency PASSED
✓ Interrupt handling latency: 3.45ms

test_streaming_stop_latency PASSED
✓ Streaming stop latency: 23.12ms
```

### 3. End-to-End Integration Tests (`test_e2e_vad_interruption.py`)

Tests complete voice interaction flow.

#### Test Classes

**TestE2EVADInterruption**
- `test_complete_voice_interaction` - Full interaction flow
- `test_vad_rejection_flow` - VAD rejection handling
- `test_interruption_during_response` - Interruption during agent response
- `test_multiple_audio_chunks_sequence` - Conversation flow

**TestE2EPerformance**
- `test_end_to_end_latency` - Measures complete latency

**TestE2EErrorHandling**
- `test_invalid_audio_format` - Invalid audio handling
- `test_session_timeout_handling` - Session timeout handling

#### Example Usage

```bash
# Run all E2E tests
pytest tests/integration/test_e2e_vad_interruption.py -v -s

# Run performance tests only
pytest tests/integration/test_e2e_vad_interruption.py::TestE2EPerformance -v
```

## Running Tests

### Using Test Runner (Recommended)

```bash
# Run all tests with summary
python tests/run_vad_tests.py

# Run with verbose output
python tests/run_vad_tests.py -v

# Run quick tests for CI/CD
python tests/run_vad_tests.py --quick

# Generate HTML reports
python tests/run_vad_tests.py --html

# Run specific suite
python tests/run_vad_tests.py --vad-only -v
```

### Using pytest Directly

```bash
# Run all VAD-related tests
pytest tests/ -k "vad or interruption" -v

# Run with coverage
pytest tests/ --cov=backend.app.core --cov-report=html

# Run specific test file
pytest tests/backend/local/core/test_vad_validation.py -v

# Run specific test
pytest tests/backend/local/core/test_vad_validation.py::TestVADValidation::test_energy_calculation -v

# Run with markers
pytest tests/ -m "asyncio" -v
```

### Makefile Integration

Add to your Makefile:

```makefile
.PHONY: test-vad
test-vad:
	python tests/run_vad_tests.py

.PHONY: test-vad-quick
test-vad-quick:
	python tests/run_vad_tests.py --quick

.PHONY: test-vad-report
test-vad-report:
	python tests/run_vad_tests.py --html
```

Then run:

```bash
make test-vad
make test-vad-quick
make test-vad-report
```

## Adding New Tests

### Adding a New VAD Test

```python
# In tests/backend/local/core/test_vad_validation.py

def test_my_new_vad_feature(self, audio_validator, audio_samples):
    """Test my new VAD feature."""
    # Arrange
    validator = audio_validator
    sample_name, audio_data = next(iter(audio_samples.items()))

    # Act
    result = validator.my_new_method(audio_data)

    # Assert
    assert result is not None
    print(f"✓ My new feature works: {result}")
```

### Adding a New Interruption Test

```python
# In tests/backend/local/core/test_interruption_flow.py

@pytest.mark.asyncio
async def test_my_interruption_scenario(self, ws_manager, mock_websocket):
    """Test my new interruption scenario."""
    # Setup
    session_id = await ws_manager.connect(mock_websocket, "test-user")

    # Test scenario
    # ...

    # Verify
    assert something
    print("✓ My scenario works")

    # Cleanup
    await ws_manager.disconnect(session_id)
```

### Adding New Audio Samples

1. Place WAV files in `tests/voice_samples/wav/`
2. Use descriptive names: `test_<feature>_<scenario>.wav`
3. Ensure 16kHz, mono, 16-bit PCM format

```bash
# Convert audio to correct format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le tests/voice_samples/wav/test_my_sample.wav
```

## Troubleshooting

### No Audio Samples Found

```
⚠ Warning: No WAV files found in tests/voice_samples/wav/
```

**Solution**: Ensure audio files exist in the correct directory:

```bash
ls tests/voice_samples/wav/
```

### WebRTC VAD Not Available

```
webrtcvad not available - WebRTC VAD validation disabled
```

**Solution**: Install webrtcvad:

```bash
uv pip install webrtcvad
```

### Tests Failing Due to Threshold Changes

If tests fail after changing VAD thresholds:

1. Check `backend/app/core/audio_validator.py` for threshold values
2. Update test expectations if thresholds changed intentionally
3. Run with `-v` to see detailed output

### AsyncIO Errors

```
RuntimeError: Event loop is closed
```

**Solution**: Ensure pytest-asyncio is installed:

```bash
uv pip install pytest-asyncio
```

### Import Errors

```
ModuleNotFoundError: No module named 'backend'
```

**Solution**: Run tests from project root:

```bash
cd /path/to/News_agent
python tests/run_vad_tests.py
```

## Performance Benchmarks

Expected performance metrics:

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| VAD Validation | < 10ms | < 50ms |
| Interrupt Latency | < 5ms | < 10ms |
| Streaming Stop | < 50ms | < 100ms |
| E2E Latency | < 2s | < 5s |

## CI/CD Integration

### GitHub Actions

```yaml
name: VAD Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements.txt
          uv pip install pytest pytest-asyncio webrtcvad
      - name: Run VAD tests
        run: python tests/run_vad_tests.py --quick
```

## Best Practices

1. **Run tests before commits**
   ```bash
   make test-vad-quick
   ```

2. **Test with real audio samples**
   - Use diverse samples (different speakers, volumes, qualities)
   - Include edge cases (very short, very long, noisy)

3. **Check performance**
   - Monitor test execution time
   - Flag slow tests with `@pytest.mark.slow`

4. **Keep tests independent**
   - Each test should clean up after itself
   - Use fixtures for shared setup

5. **Document new features**
   - Add tests for new VAD features
   - Update this guide

## Support

For issues or questions:
- Check test output with `-v` flag
- Review logs in `reports/` directory
- See [main documentation](../README.md)