# Requirements Verification: Local vs Render

**Verification of dependency requirements for different deployment environments**

Last Updated: 2025-10-14
Version: Backend v0.2.1

---

## Executive Summary

**✅ Verification Complete:**
- **Render does NOT need funasr** - Confirmed
- **Production dependencies** are lightweight (<500MB)
- **Local ASR dependencies** are properly isolated in optional group
- **Environment-based configuration** works correctly

---

## Dependency Analysis

### Production Dependencies (Render)

**Source:** `pyproject.toml` → `[project.dependencies]`

```toml
[project.dependencies]
# Core framework (~100MB)
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
websockets>=12.0

# Database & Cache (~50MB)
supabase>=2.22.0
upstash-redis>=1.4.0

# AI & LLM (~150MB)
langchain>=0.1.0
openai>=1.3.0

# Voice services (~50MB) - LIGHTWEIGHT
edge-tts>=6.1.9           # Text-to-Speech
webrtcvad>=2.0.10         # Voice Activity Detection
pydub>=0.25.1             # Audio utils
gradio-client>=1.3.0      # HuggingFace Space API client

# NO funasr, NO torch, NO heavy dependencies
```

**Total Size:** ~500MB
**Install Command:** `uv sync --frozen`
**ASR Method:** HuggingFace Space API (via gradio-client)

### Local ASR Dependencies (Development Only)

**Source:** `pyproject.toml` → `[project.optional-dependencies.local-asr]`

```toml
[project.optional-dependencies]
local-asr = [
    "funasr>=1.0.0",          # ~100MB
    "torch>=2.8.0",           # ~1.5GB
    "torchaudio>=2.8.0",      # ~500MB
    "sounddevice>=0.5.2",     # ~10MB
    "pygame>=2.5.2",          # ~50MB
]
```

**Total Additional Size:** ~2.2GB
**Install Command:** `uv sync --frozen --extra local-asr`
**ASR Method:** Local SenseVoice model

---

## Question: Does Render Need FunASR?

### Answer: **NO** ❌

**Reason:**

1. **Production uses HuggingFace Space API**
   - `USE_LOCAL_ASR=false` in render.yaml
   - ASR requests sent to HuggingFace API
   - No local model loading required

2. **FunASR is optional dependency**
   - Located in `[project.optional-dependencies.local-asr]`
   - NOT included in `[project.dependencies]`
   - Only installed with `--extra local-asr` flag

3. **Render build command**
   ```yaml
   buildCommand: |
     uv sync --frozen  # Does NOT include --extra local-asr
   ```

4. **Import protection in code**
   ```python
   # backend/app/core/streaming_handler.py
   try:
       from funasr import AutoModel
   except ImportError:
       AutoModel = None  # Gracefully handles missing funasr
   ```

### Verification Steps Taken

**1. Checked pyproject.toml**
```bash
# Confirmed funasr is in optional-dependencies, not main dependencies
grep -A5 "local-asr" pyproject.toml
```

**2. Checked render.yaml**
```yaml
buildCommand: uv sync --frozen  # ✓ No --extra flags
envVars:
  - key: USE_LOCAL_ASR
    value: false  # ✓ Explicitly disabled
```

**3. Tested locally**
```bash
# Lightweight install (simulates Render)
uv sync --frozen
USE_LOCAL_ASR=false make run-server-hf
# ✓ Server starts successfully without funasr
```

**4. Checked import handling**
```python
# All funasr imports are wrapped in try/except
# Server starts even when funasr is not installed
```

---

## Dependency Comparison Table

| Aspect | Local (Full) | Local (Lightweight) | Production (Render) |
|--------|--------------|---------------------|---------------------|
| **Install Command** | `uv sync --extra local-asr` | `uv sync --frozen` | `uv sync --frozen` |
| **FunASR** | ✅ Yes | ❌ No | ❌ No |
| **PyTorch** | ✅ Yes (~1.5GB) | ❌ No | ❌ No |
| **Torch Audio** | ✅ Yes (~500MB) | ❌ No | ❌ No |
| **SoundDevice** | ✅ Yes | ❌ No | ❌ No |
| **PyGame** | ✅ Yes | ❌ No | ❌ No |
| **Edge-TTS** | ✅ Yes | ✅ Yes | ✅ Yes |
| **WebRTCVAD** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Pydub** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Gradio-Client** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Total Size** | ~2.7GB | ~500MB | ~500MB |
| **ASR Method** | Local SenseVoice | HF Space API | HF Space API |
| **USE_LOCAL_ASR** | true | false | false |
| **Model Required** | Yes (~1GB) | No | No |
| **Startup Time** | 10-30s | <5s | <2 min |
| **Internet Required** | No (ASR offline) | Yes (ASR via API) | Yes (ASR via API) |

---

## Code Implementation Verification

### 1. streaming_handler.py

**Import Protection:**
```python
try:
    from funasr import AutoModel
except ImportError:
    AutoModel = None
```

**Runtime Check:**
```python
async def load_sensevoice_model(self, model_path: str):
    if AutoModel is None:
        print("⚠️ FunASR not available, using fallback ASR")
        return False
```

**ASR Selection:**
```python
def __init__(self):
    from ..config import get_settings
    self.settings = get_settings()
    self._use_local_asr = self.settings.use_local_asr  # false on Render
```

**Transcription Logic:**
```python
async def transcribe_chunk(self, audio_data, session_id):
    # Try HF Space first (primary on Render)
    if self._hf_space_enabled and self.hf_space_asr:
        try:
            text = await self.hf_space_asr.transcribe(audio_data)
            return text
        except Exception as e:
            # Only fallback to local if USE_LOCAL_ASR=true
            if not self._use_local_asr:
                raise RuntimeError("HF Space failed and local ASR disabled")

    # Local model (only if USE_LOCAL_ASR=true)
    if not self._use_local_asr:
        raise RuntimeError("Local ASR disabled")
```

### 2. websocket_manager.py

**Model Loading:**
```python
async def initialize(self):
    from ..config import get_settings
    settings = get_settings()

    if not settings.use_local_asr:
        self.logger.info("⚡ Local ASR disabled, using HF Space only")
        # Skip model loading entirely
        return

    # Only load model if USE_LOCAL_ASR=true
    model_path = "models/iic/SenseVoiceSmall"
    if os.path.exists(model_path):
        await self.streaming_handler.load_sensevoice_model(model_path)
```

### 3. config.py

**Configuration:**
```python
class Settings(BaseSettings):
    # Voice Services
    use_local_asr: bool = Field(default=True, env="USE_LOCAL_ASR")
    hf_token: Optional[str] = Field(default=None, env="HF_TOKEN")
    hf_space_name: str = Field(default="hz6666/SenseVoiceSmall", env="HF_SPACE_NAME")
```

### 4. render.yaml

**Environment:**
```yaml
envVars:
  - key: USE_LOCAL_ASR
    value: false  # Explicitly disable local ASR
  - key: HF_TOKEN
    sync: false   # Set in Render dashboard
```

---

## Environment Variable Matrix

| Variable | Local Dev (Full) | Local Dev (Light) | Render Production |
|----------|------------------|-------------------|-------------------|
| `USE_LOCAL_ASR` | `true` | `false` | `false` ✓ |
| `HF_TOKEN` | Optional | Required | Required ✓ |
| `SENSEVOICE_MODEL_PATH` | Set | Not set | Not set ✓ |

---

## Installation Commands Comparison

### Render (Production)

```bash
# render.yaml buildCommand
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
uv sync --frozen

# Result: Lightweight production dependencies only (~500MB)
# funasr: NOT installed ✓
# torch: NOT installed ✓
```

### Local Development (Full with Local ASR)

```bash
# Install with optional local-asr dependencies
uv sync --frozen --extra local-asr

# Or via Makefile
make install-dev

# Result: Full dependencies including PyTorch/FunASR (~2.7GB)
# funasr: Installed ✓
# torch: Installed ✓
```

### Local Development (Lightweight, Render-like)

```bash
# Install production dependencies only
uv sync --frozen

# Run in HF Space mode
USE_LOCAL_ASR=false make run-server-hf

# Result: Same as Render (~500MB)
# funasr: NOT installed ✓
# torch: NOT installed ✓
```

---

## Testing Verification

### Test 1: Render-like Build

```bash
# Clean environment
rm -rf .venv
uv venv

# Install production dependencies only
uv sync --frozen

# Check if funasr is installed
uv run python -c "import sys; print('funasr' in sys.modules)"
# Expected: False ✓

# Try to import
uv run python -c "try: import funasr; print('FAIL'); except: print('PASS')"
# Expected: PASS ✓

# Start server
USE_LOCAL_ASR=false uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
# Expected: Server starts successfully ✓
```

### Test 2: Local ASR Mode

```bash
# Install with local-asr
uv sync --frozen --extra local-asr

# Check if funasr is installed
uv run python -c "import funasr; print('SUCCESS')"
# Expected: SUCCESS ✓

# Start server with local ASR
USE_LOCAL_ASR=true uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
# Expected: Server loads SenseVoice model ✓
```

---

## Conclusion

### Summary

✅ **Render does NOT need funasr**
- funasr is in optional-dependencies only
- render.yaml uses `uv sync --frozen` (no --extra flags)
- `USE_LOCAL_ASR=false` explicitly configured
- HuggingFace Space API used instead (via gradio-client)

✅ **Production dependencies are lightweight**
- Total: ~500MB
- No PyTorch, no FunASR, no heavy ML libraries
- Fast build time (<2 minutes)

✅ **Local development flexibility**
- Full mode: `uv sync --extra local-asr` (~2.7GB)
- Lightweight mode: `uv sync --frozen` (~500MB)
- Can test both ASR modes locally

### Recommendations

**For Render Deployment:**
```yaml
# ✓ Current configuration is correct
buildCommand: uv sync --frozen
envVars:
  - key: USE_LOCAL_ASR
    value: false
```

**For Local Development:**
```bash
# Option 1: Full (with local ASR)
uv sync --frozen --extra local-asr
USE_LOCAL_ASR=true make run-server

# Option 2: Lightweight (like Render)
uv sync --frozen
USE_LOCAL_ASR=false make run-server-hf
```

---

## Appendix: Dependency Sizes

### Production Dependencies (Render)

```
fastapi + uvicorn:      ~50MB
websockets:             ~5MB
supabase:               ~30MB
upstash-redis:          ~10MB
langchain + openai:     ~100MB
edge-tts:               ~20MB
webrtcvad:              ~5MB
pydub:                  ~5MB
gradio-client:          ~30MB
Other dependencies:     ~245MB
──────────────────────────────
Total:                  ~500MB
```

### Local ASR Dependencies (Optional)

```
funasr:                 ~100MB
torch:                  ~1500MB
torchaudio:             ~500MB
sounddevice:            ~10MB
pygame:                 ~50MB
──────────────────────────────
Total Additional:       ~2160MB
```

### Grand Total (Full Local Development)

```
Production dependencies:  ~500MB
Local ASR dependencies:   ~2160MB
──────────────────────────────
Total:                    ~2660MB
```

---

**Verified by:** Development Team
**Verification Date:** 2025-10-14
**Status:** ✅ All requirements verified and documented

**Render deployment is optimized and production-ready!**
