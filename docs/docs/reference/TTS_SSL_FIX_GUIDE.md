# Edge-TTS SSL Certificate Error Fix Guide

## Error Message
```
ERROR:news_agent:Error: TTS error: Cannot connect to host api.msedgeservices.com:443 ssl:True
[SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1017)')]
```

## Root Cause
This error occurs when the SSL certificate for Microsoft's Edge TTS service (`api.msedgeservices.com`) cannot be verified. Common causes:

1. **Expired SSL certificate** on Microsoft's server
2. **Outdated certificate store** in Python (certifi package)
3. **Incorrect system date/time** on your machine
4. **Network proxy/firewall** interfering with SSL verification
5. **Outdated edge-tts library**

## Quick Fixes (Try in Order)

### Solution 1: Update Certifi Package ⭐ (Most Common Fix)

The `certifi` package provides Mozilla's root certificates. Updating it often resolves SSL issues:

```bash
uv pip install --upgrade certifi
```

Or with regular pip:
```bash
pip install --upgrade certifi
```

**Why this works**: edge-tts relies on Python's certificate store (provided by certifi) to verify SSL connections. An outdated certifi may not have the latest certificates.

### Solution 2: Update Edge-TTS Library

Microsoft may have updated the edge-tts library to handle certificate changes:

```bash
uv pip install --upgrade edge-tts
```

Check your current version:
```bash
uv pip list | grep edge-tts
```

Latest version should be 7.x.x or higher.

### Solution 3: Check System Date and Time

SSL certificates have validity periods. If your system clock is wrong, certificates will appear expired:

**macOS**:
```bash
# Check current date/time
date

# Sync time (if needed)
sudo sntp -sS time.apple.com
```

**Linux**:
```bash
# Check current date/time
date

# Sync time (if needed)
sudo ntpdate -u pool.ntp.org
```

**Ensure**:
- Date is correct
- Time zone is correct
- Time is synchronized with internet time servers

### Solution 4: Update All Dependencies

Sometimes the issue is with underlying packages:

```bash
uv pip install --upgrade certifi edge-tts aiohttp ssl
```

### Solution 5: Clear Python SSL Cache (macOS Specific)

If you're on macOS, Python may need to reinstall certificates:

```bash
# Navigate to Python's Certificates.command
/Applications/Python\ 3.10/Install\ Certificates.command

# Or manually
pip install --upgrade certifi
```

### Solution 6: Use Alternative TTS Service (Temporary Workaround)

If edge-tts continues to fail, consider switching to an alternative TTS provider:

#### Option A: Google TTS (gTTS)
```bash
uv pip install gtts
```

```python
from gtts import gTTS
import io

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()
```

#### Option B: Pyttsx3 (Offline)
```bash
uv pip install pyttsx3
```

```python
import pyttsx3

engine = pyttsx3.init()
engine.say("Hello world")
engine.runAndWait()
```

#### Option C: OpenAI TTS (Paid)
```bash
uv pip install openai
```

```python
from openai import OpenAI

client = OpenAI()
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello world!"
)
response.stream_to_file("output.mp3")
```

## Advanced Troubleshooting

### Check SSL Connection Manually

Test if you can connect to the Edge TTS service:

```python
import ssl
import socket

hostname = 'api.msedgeservices.com'
port = 443

context = ssl.create_default_context()

try:
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print(f"✅ SSL connection successful")
            print(f"   Protocol: {ssock.version()}")
            cert = ssock.getpeercert()
            print(f"   Certificate valid until: {cert['notAfter']}")
except ssl.SSLError as e:
    print(f"❌ SSL Error: {e}")
except Exception as e:
    print(f"❌ Connection Error: {e}")
```

### Bypass SSL Verification (NOT RECOMMENDED for Production)

**⚠️ Security Warning**: Only use this for testing/debugging. Never in production!

Create a custom edge-tts wrapper with SSL verification disabled:

```python
import ssl
import aiohttp
import edge_tts

# Create custom SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Use with aiohttp connector
connector = aiohttp.TCPConnector(ssl=ssl_context)

# Note: edge-tts doesn't directly support custom SSL contexts
# You would need to modify the edge-tts source or use an HTTP proxy
```

### Check Certificate Store

View certificates in your Python environment:

```python
import certifi

print(f"Certificate file location: {certifi.where()}")

# Check certificate file exists and is readable
import os
cert_path = certifi.where()
print(f"Certificate file exists: {os.path.exists(cert_path)}")
print(f"Certificate file size: {os.path.getsize(cert_path)} bytes")
```

## Implementing Alternative TTS in Your Code

If you need to switch TTS providers, here's how to modify the streaming handler:

### File: `backend/app/core/streaming_handler.py`

Add configuration for TTS provider:

```python
class StreamingVoiceHandler:
    def __init__(self):
        # ... existing code ...

        # TTS configuration
        from ..config import get_settings
        self.settings = get_settings()
        self.tts_provider = self.settings.tts_provider  # 'edge', 'gtts', 'openai'

    async def stream_tts_audio(self, text: str, **kwargs):
        """Stream TTS with fallback providers."""

        # Try primary provider
        try:
            if self.tts_provider == 'edge':
                async for chunk in self._stream_edge_tts(text, **kwargs):
                    yield chunk
            elif self.tts_provider == 'gtts':
                async for chunk in self._stream_gtts(text, **kwargs):
                    yield chunk
            # Add more providers...

        except Exception as e:
            print(f"⚠️ TTS provider {self.tts_provider} failed: {e}")

            # Fallback to alternative
            if self.tts_provider != 'gtts':
                print("   Falling back to gTTS...")
                async for chunk in self._stream_gtts(text, **kwargs):
                    yield chunk

    async def _stream_edge_tts(self, text: str, voice: str = "en-US-AriaNeural", **kwargs):
        """Edge TTS implementation."""
        # ... existing edge-tts code ...

    async def _stream_gtts(self, text: str, **kwargs):
        """Google TTS implementation."""
        from gtts import gTTS
        import io

        tts = gTTS(text=text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        # Yield in chunks
        chunk_size = 4096
        while True:
            chunk = audio_buffer.read(chunk_size)
            if not chunk:
                break
            yield chunk
```

## Environment Configuration

Add to `.env` or `backend/app/config.py`:

```bash
# TTS Configuration
TTS_PROVIDER=edge  # Options: edge, gtts, openai, pyttsx3
TTS_FALLBACK_PROVIDER=gtts  # Fallback if primary fails

# OpenAI TTS (if using)
OPENAI_API_KEY=your_openai_key_here
```

## Monitoring and Logging

Enhanced error logging:

```python
import logging

logger = logging.getLogger(__name__)

try:
    async for chunk in self.stream_tts_audio(text):
        yield chunk
except ssl.SSLError as e:
    logger.error(f"TTS SSL Error: {e}", extra={
        "error_type": "ssl_certificate",
        "service": "edge-tts",
        "hostname": "api.msedgeservices.com"
    })
    # Try fallback...
except Exception as e:
    logger.error(f"TTS Error: {e}")
```

## Long-term Solution

### Switch to Self-Hosted TTS

Consider self-hosting TTS for production:

1. **Coqui TTS** (Open Source)
   ```bash
   pip install TTS
   ```

2. **Mozilla TTS** (Open Source)
   ```bash
   pip install mozilla-tts
   ```

3. **Bark** (High Quality, Open Source)
   ```bash
   pip install git+https://github.com/suno-ai/bark.git
   ```

## Prevention

To avoid future SSL issues:

1. **Keep packages updated**:
   ```bash
   uv pip install --upgrade certifi edge-tts aiohttp
   ```

2. **Set up automated certificate monitoring**:
   ```python
   import ssl
   import socket
   from datetime import datetime

   def check_cert_expiry(hostname):
       context = ssl.create_default_context()
       with socket.create_connection((hostname, 443)) as sock:
           with context.wrap_socket(sock, server_hostname=hostname) as ssock:
               cert = ssock.getpeercert()
               expiry = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
               days_left = (expiry - datetime.now()).days
               return days_left

   # Check weekly
   days = check_cert_expiry('api.msedgeservices.com')
   if days < 30:
       print(f"⚠️ Certificate expires in {days} days!")
   ```

3. **Implement graceful degradation**:
   - Primary: Edge-TTS
   - Fallback 1: gTTS
   - Fallback 2: pyttsx3 (offline)

## Summary

**Recommended Steps**:
1. ✅ Update certifi: `uv pip install --upgrade certifi`
2. ✅ Update edge-tts: `uv pip install --upgrade edge-tts`
3. ✅ Check system date/time
4. ✅ Implement TTS fallback mechanism
5. ✅ Monitor for future SSL issues

**If Issue Persists**:
- Check edge-tts GitHub issues: https://github.com/rany2/edge-tts/issues
- Consider alternative TTS provider (gTTS, OpenAI, self-hosted)
- Report issue if it's a new problem

## Related Files

- `backend/app/core/streaming_handler.py` - TTS implementation
- `backend/app/config.py` - Configuration settings
- Requirements: `certifi`, `edge-tts`, `aiohttp`

## References

- Edge-TTS GitHub: https://github.com/rany2/edge-tts
- Certifi Documentation: https://github.com/certifi/python-certifi
- SSL Certificate Issue #129: https://github.com/rany2/edge-tts/issues/129
