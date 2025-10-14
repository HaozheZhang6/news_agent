# Hugging Face Space Test Script

This script (`test_huggingface_space.py`) tests the Hugging Face Space ASR API by sending WAV files and validating responses against expected transcripts.

## Features

- **Space Status Check**: Verifies the Space is accessible before testing
- **Audio File Testing**: Sends WAV files via base64 encoding to the Space API
- **Similarity Validation**: Compares transcripts with expected text using sequence matching
- **Multiple Sample Support**: Can test single or multiple voice samples
- **Detailed Reporting**: Shows response times, similarity scores, and pass/fail status
- **Error Handling**: Graceful handling of network errors, timeouts, and API failures

## Usage

### Basic Usage
```bash
# Test default samples
uv run python scripts/test_huggingface_space.py

# Test specific sample
uv run python scripts/test_huggingface_space.py --sample-id analysis_aapl_deeper

# Test multiple samples
uv run python scripts/test_huggingface_space.py --sample-ids "news_nvda_latest,price_aapl,analysis_aapl_deeper"

# Use custom Space URL
uv run python scripts/test_huggingface_space.py --space-url https://your-space.hf.space

# Adjust similarity threshold
uv run python scripts/test_huggingface_space.py --similarity-threshold 0.8
```

### Makefile Targets
```bash
# Test Hugging Face Space (default samples)
make test-hf-space

# Test specific sample
make test-hf-space-sample
```

## Configuration

The script uses `tests/voice_samples/voice_samples.json` to get:
- Sample IDs and expected text
- WAV file paths
- Expected entities and intents

## Expected Response Format

The Space API should return:
```json
{
  "data": ["<transcript-text>"],
  "is_generating": false,
  "duration": 0.123,
  "average_duration": 0.456
}
```

## Sample Test Results

```
🧪 Testing 1 samples against Hugging Face Space
🌐 Space URL: https://hz6666-sensevoicesmall.hf.space
📊 Similarity threshold: 70.00%

🎯 Testing sample: analysis_aapl_deeper
============================================================
📁 WAV file: tests/voice_samples/wav/test_analysis_aapl_deeper.wav
📝 Expected text: Tell me more about that Apple story
🚀 Sending request to: https://hz6666-sensevoicesmall.hf.space/api/predict/
✅ Response received (2.34s)
📝 Transcript: Tell me more about that Apple story
📊 Similarity: 100.00%

================================================================================
HUGGING FACE SPACE TEST RESULTS
================================================================================

📊 Summary: 1/1 tests passed
⏱️  Average response time: 2.34s
📈 Average similarity: 100.00%

📋 Detailed Results:
✅ analysis_aapl_deeper: PASS
   📝 Expected: Tell me more about that Apple story
   🎤 Transcript: Tell me more about that Apple story
   📊 Similarity: 100.00%
   ⏱️  Response time: 2.34s
```

## Troubleshooting

### Space Not Accessible (404)
- Check Space URL is correct
- Ensure Space has been deployed successfully
- Verify Space is not sleeping (free tier limitation)

### Low Similarity Scores
- Check audio quality and clarity
- Verify expected text matches the actual spoken content
- Consider adjusting similarity threshold

### Request Timeouts
- Free tier Spaces may have cold start delays
- Try again after a few seconds
- Consider upgrading to paid tier for better performance

### API Errors
- Check Space logs for deployment issues
- Verify model is loading correctly
- Ensure audio format is supported (WAV, OGG, OPUS)
