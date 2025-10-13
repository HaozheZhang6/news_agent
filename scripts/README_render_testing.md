# Render WebSocket Testing Script

This script tests your deployed Render server's WebSocket functionality using the same voice samples as your local integration tests.

## Usage

### Basic Usage
```bash
# Test with default sample (news_nvda_latest) and default URL
python scripts/test_render_websocket.py

# Test with your specific Render URL
python scripts/test_render_websocket.py --url https://your-app-name.onrender.com
```

### Advanced Usage
```bash
# Test specific sample
python scripts/test_render_websocket.py --sample-id price_aapl --url https://your-app.onrender.com

# Test multiple samples
python scripts/test_render_websocket.py --sample-id price_aapl,news_nvda_latest,price_tsla --url https://your-app.onrender.com

# Test with custom timeout
python scripts/test_render_websocket.py --timeout 60 --url https://your-app.onrender.com

# Only test health endpoint (skip WebSocket)
python scripts/test_render_websocket.py --health-only --url https://your-app.onrender.com
```

## Available Samples

The script uses samples from `tests/voice_samples/voice_samples.json`. Common samples include:

- `news_nvda_latest` - "What's the latest news about NVIDIA?"
- `price_aapl` - "What is the current price of Apple stock?"
- `price_nvda` - "How much is NVIDIA stock trading at?"
- `price_tsla` - "What's the price of Tesla stock?"
- `price_msft` - "Tell me the current Microsoft stock price"

## What It Tests

1. **Health Endpoint**: Checks if `/health` is accessible
2. **WebSocket Connection**: Establishes WebSocket connection to `/ws`
3. **Audio Processing**: Sends encoded OPUS audio data
4. **Response Handling**: Receives and validates audio/text responses
5. **Session Management**: Checks for session ID and transcript

## Output

The script provides detailed logging and a summary report showing:
- ✅/❌ Test status for each sample
- Response times
- Number of audio chunks received
- Session ID and transcript (if available)
- Overall pass/fail summary

## Troubleshooting

If tests fail:
1. Check that your Render deployment is running
2. Verify the URL is correct
3. Check Render logs for errors
4. Ensure environment variables are set correctly
5. Test with `--health-only` first to verify basic connectivity
